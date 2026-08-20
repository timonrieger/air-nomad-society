<script lang="ts">
	const features = [
		{
			title: 'Get Personalized Flight Deals',
			text: "Deals are tailored based on your preferences. No need for frequent searches - you'll get flight options that fit your travel interests.",
			img: 'https://images.unsplash.com/photo-1567927663055-efed28734f1f?w=800&auto=format&fit=crop&q=60',
			alt: 'Mountain with ocean view'
		},
		{
			title: 'Discover Unusual Destinations',
			text: 'Find unique travel spots easily. Alongside deals for favorite destinations, discover new places you may not have considered.',
			img: 'https://images.unsplash.com/photo-1615449551620-d4b780ef9387?w=800&auto=format&fit=crop&q=60',
			alt: 'Sailing boat on the ocean'
		},
		{
			title: 'No More Lengthy Flight Searches',
			text: 'With a single weekly email, get relevant flight details without needing to conduct lengthy searches.',
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
			a: 'Flight deal emails are sent once a week, covering deals for both favorite and random destinations.'
		},
		{
			q: 'What does "Favorite Destinations" mean?',
			a: 'Mark certain countries as favorites to receive deals specifically for those locations each week.'
		},
		{
			q: 'Will I get flight deals for non-favorite destinations?',
			a: "Even if you haven't marked certain places as favorites, you'll still get occasional deals for random destinations."
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
		content="Join to receive weekly emails with flight deals. One email per week, focused on delivering relevant flight information directly to your inbox."
	/>
</svelte:head>

<section class="py-20 text-center">
	<h1 class="mb-3 text-5xl font-bold">Air Nomad Society</h1>
	<p class="mx-auto mb-8 max-w-xl text-lg text-ink-muted">
		Get the best flight deals directly in your inbox, fully automated, just one email per week.
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
