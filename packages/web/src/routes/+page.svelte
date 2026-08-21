<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDeals, type WallDeal } from '$lib/api';

	let deals = $state<WallDeal[]>([]);

	onMount(async () => {
		// The wall is a garnish on the landing page: if the API is down the
		// section simply stays hidden.
		deals = await fetchDeals().catch(() => []);
	});

	const foundOn = (deal: WallDeal) => {
		const [, month, day] = deal.found_on.split('-');
		return `${day}.${month}.`;
	};

	type Stat = { value: string; label: string };
	type Step = { index: string; title: string; text: string };
	type Benefit = { title: string; text: string };
	type FaqItem = { q: string; a: string };

	// Counts mirror packages/app/src/data.json — the reference data the search runs on.
	const stats: Stat[] = [
		{ value: '450+', label: 'departure cities' },
		{ value: '197', label: 'destination countries' },
		{ value: '2 min', label: 'to set up, no account' }
	];

	const steps: Step[] = [
		{
			index: '01',
			title: 'Set your flying style',
			text: 'Departure cities, favorite countries, trip length and how far ahead you plan. Two minutes, no account, changeable from every email.'
		},
		{
			index: '02',
			title: 'We do the searching',
			text: 'Every cycle we price your countries out of each of your cities, compare them against what the route usually costs and rank what is left.'
		},
		{
			index: '03',
			title: 'One email, already sorted',
			text: 'Weekly, every two weeks or monthly — whichever you picked. Best deals first, each with its price, its usual price and why it made the cut.'
		}
	];

	const benefits: Benefit[] = [
		{
			title: 'Personalized, with a reason',
			text: 'Deals are picked for your favorite countries, trip length and departure cities. Each one carries a short note on why it beat the alternatives.'
		},
		{
			title: 'Discoveries, not repeats',
			text: 'Alongside your favorites, every digest mixes in surprise destinations. It remembers what you have seen, so it never cycles the same places week after week.'
		},
		{
			title: 'A good price on sight',
			text: 'Every deal shows what the route typically costs and outstanding fares are badged. One short email and no more comparison tabs for your flights.'
		}
	];

	const faq: FaqItem[] = [
		{
			q: 'What is the pricing for Air Nomad Society?',
			a: 'The deal digest is free. If you book through a deal link, our booking partner may pay us a small affiliate commission at no extra cost to you. Your data is never sold or used for anything but your digest.'
		},
		{
			q: 'Where can I fly from?',
			a: 'Deals depart from the cities you pick — more than 450 departure cities worldwide are supported. Start typing yours in the subscribe form to check.'
		},
		{
			q: 'How do I book a deal?',
			a: 'Every deal in the email links straight to the fare on our booking partner’s site, where you book directly — we never sell tickets ourselves. Prices are round-trip per person as found.'
		},
		{
			q: 'What is the difference to Skyscanner and Co.?',
			a: "Unlike traditional platforms, Air Nomad Society offers a direct approach. Deals are curated for you and sent automatically, so you don't need to actively search or compare."
		},
		{
			q: 'How often will I receive flight deal emails?',
			a: 'Flight deal emails are sent weekly, every two weeks or monthly — your choice: the best deals found across your favorite countries and a few surprise discoveries, ranked by quality.'
		},
		{
			q: 'What does "Favorite Destinations" mean?',
			a: 'Mark certain countries as favorites and every email includes the best deal we found for each of them. They are optional — without any, your digest is all surprise discoveries.'
		},
		{
			q: 'Will I get flight deals for non-favorite destinations?',
			a: "Yes. Alongside your favorites, emails mix in discovery deals of surprising destinations you haven't marked, labeled with a discovery badge."
		},
		{
			q: 'Can I exclude regions or countries?',
			a: "Yes. Exclude countries you never want as surprise discoveries — pick a whole region to toggle all of its countries at once. Your favorites aren't affected."
		},
		{
			q: 'Will I see the same deals every time?',
			a: 'No. The digest remembers what you have already been sent: repeats only come back on clearly better prices and repeating countries rotate their cities.'
		},
		{
			q: 'Can I depart from more than one city?',
			a: 'Yes, you can pick multiple departure cities. Every destination is searched from each of them, the best deal wins, and each card shows which city it flies from.'
		},
		{
			q: 'How far ahead do the flight deals cover?',
			a: 'You can customize your search range up to 1 year in advance.'
		}
	];
</script>

<svelte:head>
	<title>Personalized Flight Deals via Email | Air Nomad Society</title>
	<meta
		name="description"
		content="Join to receive emails with flight deals at the pace you choose, focused on delivering relevant flight information directly to your inbox."
	/>
</svelte:head>

<section class="relative pt-20 pb-6 text-center">
	<div
		class="pointer-events-none absolute inset-x-0 -top-20 -z-10 mx-auto h-64 max-w-xl rounded-full bg-accent/20 blur-3xl"
	></div>
	<h1 class="mb-3 text-5xl font-bold">Air Nomad Society</h1>
	<p class="mx-auto mb-8 max-w-xl text-lg text-ink-muted">
		Get the best flight deals directly in your inbox, fully automated, at the pace you choose.
	</p>
	<div class="flex items-center justify-center gap-6">
		<a class="btn" href="/subscribe">Subscribe For Free</a>
		<a
			class="text-ink-muted underline underline-offset-4 hover:text-ink"
			href="/sample-digest.html"
			target="_blank">See a sample email</a
		>
	</div>
	<p class="mt-5 text-sm text-ink-muted">
		Free · 450+ departure cities worldwide · unsubscribe anytime
	</p>
	<dl class="mx-auto mt-14 grid max-w-lg grid-cols-3 gap-6">
		{#each stats as stat (stat.label)}
			<div>
				<dt class="text-2xl font-bold text-accent-bright sm:text-3xl">{stat.value}</dt>
				<dd class="mt-1 text-sm text-ink-muted">{stat.label}</dd>
			</div>
		{/each}
	</dl>
</section>

<section class="my-20">
	<p class="eyebrow">How it works</p>
	<h2 class="mt-2 max-w-2xl text-3xl font-bold">Set it up once, then just read your inbox</h2>
	<div class="mt-10 grid gap-8 sm:grid-cols-3 sm:gap-10">
		{#each steps as step (step.index)}
			<div class="border-t-2 border-accent pt-5">
				<span class="text-sm font-bold tracking-widest text-accent-bright">{step.index}</span>
				<h3 class="mt-2 text-lg font-semibold">{step.title}</h3>
				<p class="mt-2 text-sm text-ink-muted">{step.text}</p>
			</div>
		{/each}
	</div>
</section>

{#if deals.length > 0}
	<section class="my-20">
		<p class="eyebrow">Recently sent</p>
		<h2 class="mt-2 text-3xl font-bold">Get flights like these</h2>
		<p class="mt-2 mb-6 max-w-2xl text-ink-muted">
			Every digest is picked for its subscriber's own cities and favorite countries. Prices are
			round-trip per person as found; good fares move fast.
		</p>
		<div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
			{#each deals as deal (deal)}
				<a
					class="group block overflow-hidden rounded-xl border border-line bg-raised transition hover:-translate-y-1 hover:border-ink-muted hover:no-underline"
					href={deal.link}
					target="_blank"
					rel="sponsored noopener"
				>
					<div class="relative overflow-hidden">
						<img
							class="h-40 w-full object-cover transition-transform duration-300 group-hover:scale-105"
							src={deal.image_url}
							alt={deal.destination}
							loading="lazy"
						/>
						{#if deal.badge}
							<span
								class="absolute top-3 left-3 rounded-full border border-line bg-raised px-2.5 py-0.5 text-xs font-semibold"
							>
								{deal.badge}
							</span>
						{/if}
					</div>
					<div class="p-5">
						<h3 class="font-semibold text-ink">{deal.departure_city} – {deal.destination}</h3>
						<p class="mt-3 text-xl font-bold text-accent-bright">
							{deal.price}
							{deal.currency}
							{#if deal.savings_percent != null && deal.usual_price != null}
								<span class="text-sm font-normal text-ink-muted">
									<s>usually ~{deal.usual_price} {deal.currency}</s>
								</span>
							{/if}
						</p>
						<p class="mt-1 text-xs text-ink-muted">found {foundOn(deal)}</p>
					</div>
				</a>
			{/each}
		</div>
		<p class="mt-8 text-center">
			<a class="btn" href="/subscribe">Get deals like these in your inbox</a>
		</p>
	</section>
{/if}

<section class="my-20">
	<p class="eyebrow">Benefits</p>
	<h2 class="mt-2 max-w-2xl text-3xl font-bold">Why the digest is worth opening</h2>
	<dl class="mt-8 divide-y divide-line border-y border-line">
		{#each benefits as benefit (benefit.title)}
			<div class="grid gap-2 py-6 sm:grid-cols-3 sm:gap-8">
				<dt class="text-lg font-semibold text-ink">{benefit.title}</dt>
				<dd class="text-ink-muted sm:col-span-2">{benefit.text}</dd>
			</div>
		{/each}
	</dl>
</section>

<section class="my-20">
	<p class="eyebrow">FAQ</p>
	<h2 class="mt-2 mb-6 text-3xl font-bold">Everything else</h2>
	<div class="divide-y divide-line overflow-hidden rounded-xl border border-line">
		{#each faq as item (item.q)}
			<details class="group" name="faq">
				<summary
					class="flex cursor-pointer list-none items-center justify-between gap-4 bg-raised px-5 py-3.5 text-base text-ink hover:bg-gray-800 [&::-webkit-details-marker]:hidden"
				>
					{item.q}
					<span
						class="text-xl leading-none text-accent-bright transition-transform group-open:rotate-45"
						aria-hidden="true">+</span
					>
				</summary>
				<p class="px-5 py-3.5 text-ink-muted">{item.a}</p>
			</details>
		{/each}
	</div>
</section>

<section
	class="my-20 rounded-2xl border border-accent/40 bg-accent/10 px-6 py-12 text-center"
>
	<h2 class="text-3xl font-bold">Your next trip is already on sale</h2>
	<p class="mx-auto mt-3 max-w-xl text-ink-muted">
		Somewhere out there a fare just dropped. Set your preferences once and we will tell you about it.
	</p>
	<p class="mt-7">
		<a class="btn" href="/subscribe">Subscribe For Free</a>
	</p>
	<p class="mt-5 text-sm text-ink-muted">
		No account · no spam · unsubscribe anytime
	</p>
</section>
