<script lang="ts">
	const features = [
		{
			title: 'Personalized Deals, With a Reason',
			text: 'Deals are picked for your favorite countries, travel dates and departure cities. Each one carries a short note on why it beat the alternatives.',
			img: 'https://images.unsplash.com/photo-1567927663055-efed28734f1f?w=800&auto=format&fit=crop&q=60',
			alt: 'Mountain with ocean view'
		},
		{
			title: 'Discover Unusual Destinations',
			text: 'Alongside your favorites, every digest mixes in surprise discoveries. It remembers what you have seen, so it never cycles the same places week after week.',
			img: 'https://images.unsplash.com/photo-1615449551620-d4b780ef9387?w=800&auto=format&fit=crop&q=60',
			alt: 'Sailing boat on the ocean'
		},
		{
			title: 'Know a Good Price on Sight',
			text: 'Every deal shows what the route typically costs and outstanding deals are badged. One short email and no more comparison tabs for your flights.',
			img: 'https://images.unsplash.com/photo-1609948679766-a6d38be3bae4?w=800&auto=format&fit=crop&q=60',
			alt: 'Beach'
		}
	];

	const faq = [
		{
			q: 'What is the pricing for Air Nomad Society?',
			a: 'Air Nomad Society is completely free to join and use.'
		},
		{
			q: 'What is the difference to Skyscanner and Co.?',
			a: "Unlike traditional platforms, Air Nomad Society offers a direct approach. Deals are curated for you and sent automatically, so you don't need to actively search or compare."
		},
		{
			q: 'How often will I receive flight deal emails?',
			a: "Flight deal emails are sent weekly — or every two weeks, if you prefer: the best deals found across your favorite countries and a few surprise discoveries, ranked by quality."
		},
		{
			q: 'What does "Favorite Destinations" mean?',
			a: 'Mark certain countries as favorites and every email includes the best deal we found for each of them.'
		},
		{
			q: 'Will I get flight deals for non-favorite destinations?',
			a: "Yes. Alongside your favorites, emails mix in discovery deals of surprising destinations you haven't marked, labeled with a discovery badge."
		},
		{
			q: 'Will I see the same deals every time?',
			a: 'No. The digest remembers what you have already been sent: repeats only come back on clearly better prices and repeating countries rotate their cities.'
		},
		{
			q: 'What does "typically ~X" under a price mean?',
			a: "That's what the route usually costs, from our own recent search history. The percentage shows how far below typical today's fare is, and the best savings earn a price badge."
		},
		{
			q: 'Why does each deal have a little note on it?',
			a: 'Every deal can carry a one-line reason, written for you: why it was picked, what it beat, and how it fits your preferences.'
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
		content="Join to receive emails with flight deals, weekly or biweekly, focused on delivering relevant flight information directly to your inbox."
	/>
</svelte:head>

<section class="py-20 text-center">
	<h1 class="mb-3 text-5xl font-bold">Air Nomad Society</h1>
	<p class="mx-auto mb-8 max-w-xl text-lg text-ink-muted">
		Get the best flight deals directly in your inbox, fully automated, at the pace you choose.
	</p>
	<a class="btn" href="/subscribe">Subscribe For Free</a>
</section>

<section>
	<h2 class="mb-4 text-2xl font-semibold">Benefits</h2>
	<div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
		{#each features as feature (feature.title)}
			<article class="overflow-hidden rounded-xl border border-line bg-raised">
				<img class="h-40 w-full object-cover" src={feature.img} alt={feature.alt} loading="lazy" />
				<div class="p-5">
					<h3 class="mb-1 font-semibold">{feature.title}</h3>
					<p class="text-sm text-ink-muted">{feature.text}</p>
				</div>
			</article>
		{/each}
	</div>
</section>

<section>
	<h2 class="mt-12 mb-4 text-2xl font-semibold">FAQ</h2>
	<div class="divide-y divide-line overflow-hidden rounded-xl border border-line">
		{#each faq as item (item.q)}
			<details name="faq">
				<summary
					class="cursor-pointer list-none bg-raised px-5 py-3.5 text-base text-ink hover:bg-gray-800 [&::-webkit-details-marker]:hidden"
				>
					{item.q}
				</summary>
				<p class="px-5 py-3.5 text-ink-muted">{item.a}</p>
			</details>
		{/each}
	</div>
</section>
