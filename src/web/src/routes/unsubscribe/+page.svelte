<script lang="ts">
	import TokenAction from '$lib/components/TokenAction.svelte';
</script>

<svelte:head>
	<title>Unsubscribe | Air Nomad Society</title>
</svelte:head>

<h1 class="page-title">Unsubscribe</h1>

<TokenAction endpoint="/unsubscribe" pending="Unsubscribing…">
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
