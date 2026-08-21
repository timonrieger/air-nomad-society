<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import type { Snippet } from 'svelte';
	import Loader from '$lib/components/Loader.svelte';
	import { fetchUnsubscribeTarget, tokenAction, tokenFromUrl } from '$lib/api';

	let {
		endpoint,
		pending,
		success,
		failure,
		confirm
	}: {
		endpoint: '/confirm' | '/unsubscribe';
		pending: string;
		success: Snippet;
		failure: Snippet;
		/** Given, the action waits for the reader: it renders the resolved
		 * address and the callback that performs the request. Omitted, the
		 * action runs on mount. */
		confirm?: Snippet<[string, () => void]>;
	} = $props();

	type Status = 'looking-up' | 'idle' | 'pending' | 'ok' | 'failed';

	// untrack: which snippets a page passes is fixed, so the initial value
	// is the whole story — reading it reactively would mean nothing.
	let status = $state<Status>(untrack(() => (confirm ? 'looking-up' : 'pending')));
	let messages = $state<string[]>([]);
	let email = $state('');
	let token = '';

	async function run() {
		status = 'pending';
		const result = await tokenAction(endpoint, token);
		status = result.ok ? 'ok' : 'failed';
		messages = result.messages;
	}

	onMount(async () => {
		const fromUrl = tokenFromUrl();
		if (!fromUrl) {
			status = 'failed';
			messages = ['This link is missing its token.'];
			return;
		}
		token = fromUrl;
		if (!confirm) return run();
		// Resolving the address first both names it in the prompt and rules
		// out a dead link before anyone is asked to confirm anything.
		const target = await fetchUnsubscribeTarget(token);
		if (target === null) {
			status = 'failed';
			messages = ['This link is invalid or the subscription no longer exists.'];
			return;
		}
		email = target;
		status = 'idle';
	});
</script>

{#if status === 'looking-up'}
	<Loader label="Checking your link…" />
{:else if status === 'idle'}
	{@render confirm!(email, run)}
{:else if status === 'pending'}
	<Loader label={pending} />
{:else}
	{#each messages as message (message)}
		<div class="banner {status === 'ok' ? 'banner-success' : 'banner-error'}">{message}</div>
	{/each}
	{#if status === 'ok'}{@render success()}{:else}{@render failure()}{/if}
{/if}
