<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { browser } from '$app/environment';
	import {
		type Cadence,
		fetchRefData,
		fetchSubscription,
		type RefData,
		saveSubscription,
		tokenFromUrl,
		UNREACHABLE
	} from '$lib/api';
	import Field from '$lib/components/Field.svelte';
	import Loader from '$lib/components/Loader.svelte';
	import SelectMenu from '$lib/components/SelectMenu.svelte';

	let refdata = $state<RefData | null>(null);
	// Read the token during hydration (never at prerender time) so the
	// loading screen replaces the form before the first client paint.
	const urlToken = browser ? tokenFromUrl() : null;
	let token = $state<string | null>(urlToken);
	let resolving = $state(urlToken !== null);
	let updating = $state(false);
	let banner = $state<{ ok: boolean; lines: string[] } | null>(null);
	let loadFailed = $state(false);
	let submitting = $state(false);

	let username = $state('');
	let email = $state('');
	let departureAirports = $state<string[]>([]);
	let currency = $state('');
	let minNights = $state(3);
	let maxNights = $state(14);
	let minDaysAhead = $state(14);
	let maxDaysAhead = $state(180);
	let cadence = $state<Cadence>('weekly');
	let includeDiscoveries = $state(true);
	let favorites = $state<string[]>([]);
	let excluded = $state<string[]>([]);

	let bannerEl = $state<HTMLDivElement | undefined>();
	let advancedOpen = $state(false);

	const toItems = (values: string[]) => values.map((v) => ({ value: v, label: v }));
	const cityItems = $derived(
		(refdata?.cities ?? []).map((c) => ({ value: c.code, label: `${c.city} (${c.code})` }))
	);
	const currencyItems = $derived(toItems(refdata?.currencies ?? []));
	const countryItems = $derived(toItems(refdata?.countries ?? []));
	const countryGroups = $derived(
		Object.entries(refdata?.regions ?? {}).map(([region, countries]) => ({
			label: region,
			items: toItems(countries)
		}))
	);
	const cadenceItems = [
		{ value: 'weekly', label: 'Every week' },
		{ value: 'biweekly', label: 'Every two weeks' },
		{ value: 'monthly', label: 'Every month' }
	];

	onMount(async () => {
		const loaded = await Promise.all([
			fetchRefData(),
			token ? fetchSubscription(token) : null
		]).catch(() => null);
		if (!loaded) {
			loadFailed = true;
			resolving = false;
			return;
		}
		const [data, current] = loaded;
		refdata = data;
		if (token && !current) {
			banner = {
				ok: false,
				lines: [
					'This link is invalid or the subscription no longer exists. You can subscribe again below.'
				]
			};
			token = null;
		}
		if (current) {
			updating = true;
			advancedOpen = true;
			username = current.username;
			email = current.email;
			departureAirports = current.departure_airports;
			currency = current.currency;
			minNights = current.min_nights;
			maxNights = current.max_nights;
			minDaysAhead = current.min_days_ahead;
			maxDaysAhead = current.max_days_ahead;
			cadence = current.cadence;
			includeDiscoveries = current.include_discoveries;
			favorites = current.favorites;
			excluded = current.excluded;
		}
		resolving = false;
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		submitting = true;
		banner = null;
		// Now that the API decides what is valid, an unreachable API is the one
		// failure the reader can neither see nor retry past.
		const errors = await saveSubscription(
			{
				username,
				email,
				departure_airports: departureAirports,
				currency,
				min_nights: minNights,
				max_nights: maxNights,
				min_days_ahead: minDaysAhead,
				max_days_ahead: maxDaysAhead,
				cadence,
				include_discoveries: includeDiscoveries,
				favorite_countries: favorites,
				excluded_countries: excluded
			},
			token
		).catch(() => [
			'Something went wrong reaching the server. Check your connection and try again.'
		]);
		submitting = false;
		banner = errors.length
			? { ok: false, lines: errors }
			: {
					ok: true,
					lines: [
						updating
							? 'Your preferences were changed successfully.'
							: `Almost there! We sent a confirmation link to ${email} — click it to start receiving deals.`
					]
				};
		await tick();
		bannerEl?.scrollIntoView({ behavior: 'smooth', block: 'center' });
	}
</script>

<svelte:head>
	<title>Subscribe | Air Nomad Society</title>
	<meta
		name="description"
		content="Join the Air Nomad Society and receive the best flight deals directly in your inbox. Sign up now for free!"
	/>
</svelte:head>

<h1 class="page-title">
	{token ? 'Update your preferences' : 'Become an Air Nomad'}
</h1>

{#if resolving}
	<Loader label="Loading your preferences…" />
{:else if loadFailed}
	<div class="banner banner-error">{UNREACHABLE}</div>
{:else}
	{#if banner}
		<div bind:this={bannerEl} class="banner {banner.ok ? 'banner-success' : 'banner-error'}">
			{#each banner.lines as line (line)}
				<div>{line}</div>
			{/each}
		</div>
	{/if}

	<form onsubmit={submit}>
		<div class="my-6 grid gap-4 sm:grid-cols-2">
			<Field required label="Username" hint="Used to personalize your emails.">
				<input
					class="input"
					required
					minlength=3
					maxlength=20
					bind:value={username}
				/>
			</Field>
			<Field
				required
				label={updating ? 'Email (cannot be changed)' : 'Email'}
				hint="Where your deal emails land."
			>
				<input class="input" type="email" required disabled={updating} bind:value={email} />
			</Field>
			<Field
				required
				label="Departure cities"
				hint="Pick up to 3. Every deal flies from one of these; the best deal across them wins."
			>
				<SelectMenu
					items={cityItems}
					placeholder="Select cities"
					multiple
					bind:value={departureAirports}
				/>
			</Field>
			<Field required label="Currency" hint="Prices are shown in this currency.">
				<SelectMenu items={currencyItems} placeholder="Select a currency" bind:value={currency} />
			</Field>
		</div>
		<details bind:open={advancedOpen} class="mb-6 overflow-hidden rounded-xl border border-line">
			<summary
				class="cursor-pointer list-none bg-raised px-5 py-3.5 hover:bg-gray-800 [&::-webkit-details-marker]:hidden"
			>
				<span class="font-semibold">Advanced configuration</span>
				<span class="block text-sm text-ink-muted">
					Trip length, timing, cadence and destination preferences — all preset with sensible
					defaults.
				</span>
			</summary>
			<div class="grid gap-4 p-5 sm:grid-cols-2">
				<Field required label="Search from (days ahead)" hint="Search starts this many days from now.">
					<input
					class="input"
					type="number"
					min=1
					max=365
					required
					bind:value={minDaysAhead}
					/>
				</Field>
				<Field required label="Search to (days ahead)" hint="Search ends this many days from now.">
					<input
					class="input"
					type="number"
					min=1
					max=365
					required
					bind:value={maxDaysAhead}
					/>
				</Field>
				<Field required label="Minimum nights" hint="Shortest trip length, in nights.">
					<input class="input" type="number" min=1 required bind:value={minNights} />
				</Field>
				<Field required label="Maximum nights" hint="Longest trip length, in nights.">
					<input
						class="input"
						type="number"
						min={minNights}
						max={maxDaysAhead - minDaysAhead}
						required
						bind:value={maxNights}
					/>
				</Field>
				<Field required label="Cadence" hint="How often your deal email arrives.">
					<SelectMenu items={cadenceItems} bind:value={cadence} />
				</Field>
				<div class="flex flex-col gap-1.5">
					<span class="text-sm text-ink-muted">Surprise discoveries</span>
					<label class="flex cursor-pointer items-center gap-2 py-2">
						<input
							type="checkbox"
							class="size-4 shrink-0 cursor-pointer accent-accent"
							bind:checked={includeDiscoveries}
						/>
						<span class="text-sm text-ink">
							Mix a few surprise destinations in alongside my favorites
						</span>
					</label>
				</div>
				<Field
					label="Favorite destinations"
					hint="Optional — pick up to 10. Every digest guarantees a deal for each favorite; without any, it is all discoveries."
				>
					<SelectMenu items={countryItems} placeholder="Select countries" multiple bind:value={favorites} />
				</Field>
				<Field
					label="Exclude from discoveries"
					hint="Never picked as surprise discoveries. Favorites are unaffected. Pick a region to toggle all its countries."
				>
					<SelectMenu
						groups={countryGroups}
						placeholder="Select countries or regions"
						multiple
						bind:value={excluded}
					/>
				</Field>
			</div>
		</details>
		<button class="btn" type="submit" disabled={submitting}>
			{updating ? 'Update Preferences' : 'Join Air Nomad Society'}
		</button>
	</form>
{/if}
