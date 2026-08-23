<script lang="ts">
	import TokenAction from '$lib/components/TokenAction.svelte';
</script>

<svelte:head>
	<title>Confirm Subscription | Air Nomad Society</title>
</svelte:head>

<h1 class="page-title">Confirm your subscription</h1>

<TokenAction endpoint="/confirm" pending="Confirming…">
	{#snippet success()}
		<p>
			You're all set — nothing else to do. Your first flight deals land in your inbox within the
			next few days. Happy travels!
		</p>
	{/snippet}
	{#snippet failure()}
		<p>
			The link may be invalid or the pending subscription may have expired. You can
			<a href="/subscribe">subscribe again</a> to receive a fresh confirmation email.
		</p>
	{/snippet}
</TokenAction>
