<script lang="ts">
	import { onMount } from 'svelte';
	import { API_URL, errorMessages } from '$lib/api';

	let status = $state<'pending' | 'ok' | 'failed'>('pending');
	let messages = $state<string[]>([]);

	onMount(async () => {
		const token = new URLSearchParams(location.search).get('token');
		if (!token) {
			status = 'failed';
			messages = ['This link is missing its token.'];
			return;
		}
		const response = await fetch(`${API_URL}/unsubscribe?token=${encodeURIComponent(token)}`);
		const body = await response.json();
		if (response.ok) {
			status = 'ok';
			messages = [body.detail as string];
		} else {
			status = 'failed';
			messages = errorMessages(body);
		}
	});
</script>

<svelte:head>
	<title>Unsubscribe | Air Nomad Society</title>
</svelte:head>

<h1 class="mt-10 text-3xl font-bold">Unsubscribe</h1>

{#if status === 'pending'}
	<p class="mt-4 text-ink-muted">Unsubscribing…</p>
{:else}
	{#each messages as message (message)}
		<div class="banner {status === 'ok' ? 'banner-success' : 'banner-error'}">{message}</div>
	{/each}
	{#if status === 'ok'}
		<p>
			Unsubscribed by mistake? You can <a href="/subscribe">subscribe again</a> at any time.
		</p>
	{:else}
		<p>
			You may already be unsubscribed. To join again, head to the
			<a href="/subscribe">subscription page</a>.
		</p>
	{/if}
{/if}
