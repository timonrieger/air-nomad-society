<script lang="ts">
	import TokenAction from '$lib/components/TokenAction.svelte';
</script>

<svelte:head>
	<title>Unsubscribe | Air Nomad Society</title>
</svelte:head>

<h1 class="page-title">Unsubscribe</h1>

<TokenAction endpoint="/unsubscribe" pending="Unsubscribing…">
	{#snippet confirm(email: string, run: () => void)}
		<p class="mt-4 text-ink-muted">
			This removes <strong class="font-semibold text-ink">{email}</strong> along with the
			preferences saved with it — departure cities, favorites and cadence. Deal emails stop right
			away, and nothing is kept to restore later.
		</p>
		<button class="btn mt-6" onclick={run}>Yes, unsubscribe me</button>
	{/snippet}
	{#snippet success()}
		<p>
			Unsubscribed by mistake? You can <a href="/subscribe">subscribe again</a> at any time.
		</p>
	{/snippet}
	{#snippet failure()}
		<p>
			You may already be unsubscribed. To join again, head to the
			<a href="/subscribe">subscription page</a>.
		</p>
	{/snippet}
</TokenAction>
