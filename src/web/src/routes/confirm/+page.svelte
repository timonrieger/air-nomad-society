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
		const response = await fetch(`${API_URL}/confirm?token=${encodeURIComponent(token)}`);
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
	<title>Confirm Subscription | Air Nomad Society</title>
</svelte:head>

<h1 class="mt-10 text-3xl font-bold">Confirm your subscription</h1>

{#if status === 'pending'}
	<p class="mt-4 text-ink-muted">Confirming…</p>
{:else}
	{#each messages as message (message)}
		<div class="banner {status === 'ok' ? 'banner-success' : 'banner-error'}">{message}</div>
	{/each}
	{#if status === 'ok'}
		<p>Your first weekly digest arrives with the next send-out. Happy travels!</p>
	{:else}
		<p>
			The link may be invalid or the pending subscription may have expired. You can
			<a href="/subscribe">subscribe again</a> to receive a fresh confirmation email.
		</p>
	{/if}
{/if}
