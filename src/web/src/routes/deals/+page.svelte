<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDeals, type WallDeal } from '$lib/api';

	let deals = $state<WallDeal[] | null>(null);

	onMount(async () => {
		deals = await fetchDeals();
	});

	const route = (deal: WallDeal) =>
		`${deal.departure_city} → ${deal.arrival_city ?? deal.arrival_country}`;

	const foundOn = (deal: WallDeal) => {
		const [, month, day] = deal.found_on.split('-');
		return `found ${day}.${month}.`;
	};
</script>

<svelte:head>
	<title>Recent Deals | Air Nomad Society</title>
	<meta
		name="description"
		content="Deals recently found for Air Nomad Society subscribers — real routes, real prices, and how far below typical they were."
	/>
</svelte:head>

<section class="py-12 text-center">
	<h1 class="mb-3 text-4xl font-bold">Found for our subscribers</h1>
	<p class="mx-auto max-w-xl text-lg text-ink-muted">
		A peek at the deals that went out recently — every subscriber's digest is picked for their own
		cities and favorite countries.
	</p>
</section>

{#if deals === null}
	<p class="py-8 text-center text-ink-muted">Loading recent deals…</p>
{:else if deals.length === 0}
	<p class="py-8 text-center text-ink-muted">
		The next digests are on their way — check back after Monday.
	</p>
{:else}
	<div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
		{#each deals as deal}
			<article class="rounded-xl border border-line bg-raised p-5">
				<div class="mb-2 flex flex-wrap gap-1.5 text-xs">
					{#if deal.badge}
						<span class="rounded-full border border-line px-2.5 py-0.5 font-semibold">
							{deal.badge}
						</span>
					{/if}
					<span class="rounded-full border border-line px-2.5 py-0.5 text-ink-muted">
						{foundOn(deal)}
					</span>
				</div>
				<h2 class="font-semibold">{route(deal)}</h2>
				<p class="text-sm text-ink-muted">{deal.arrival_country}</p>
				<p class="mt-3 text-xl font-bold text-accent-bright">
					{Math.round(deal.price)}
					{deal.currency}
					{#if deal.savings_percent !== null}
						<span class="text-sm font-semibold text-ink-muted">(−{deal.savings_percent}%)</span>
					{/if}
				</p>
			</article>
		{/each}
	</div>
{/if}

<section class="py-14 text-center">
	<p class="mb-5 text-lg text-ink-muted">Want deals like these picked for your cities?</p>
	<a class="btn" href="/subscribe">Subscribe For Free</a>
</section>
