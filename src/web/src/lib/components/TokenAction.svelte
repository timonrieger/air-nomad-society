<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import { tokenAction, tokenFromUrl } from '$lib/api';

	let {
		endpoint,
		pending,
		success,
		failure
	}: {
		endpoint: '/confirm' | '/unsubscribe';
		pending: string;
		success: Snippet;
		failure: Snippet;
	} = $props();

	let status = $state<'pending' | 'ok' | 'failed'>('pending');
	let messages = $state<string[]>([]);

	onMount(async () => {
		const token = tokenFromUrl();
		if (!token) {
			status = 'failed';
			messages = ['This link is missing its token.'];
			return;
		}
		const result = await tokenAction(endpoint, token);
		status = result.ok ? 'ok' : 'failed';
		messages = result.messages;
	});
</script>

{#if status === 'pending'}
	<p class="mt-4 text-ink-muted">{pending}</p>
{:else}
	{#each messages as message (message)}
		<div class="banner {status === 'ok' ? 'banner-success' : 'banner-error'}">{message}</div>
	{/each}
	{#if status === 'ok'}{@render success()}{:else}{@render failure()}{/if}
{/if}
