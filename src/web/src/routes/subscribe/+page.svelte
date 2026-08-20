<script lang="ts">
	import { onMount } from 'svelte';
	import Field from '$lib/components/Field.svelte';
	import SelectMenu from '$lib/components/SelectMenu.svelte';
	import { API_URL, errorMessages, type RefData, type Subscription } from '$lib/api';

	let refdata = $state<RefData | null>(null);
	let token = $state<string | null>(null);
	let updating = $state(false);
	let invalidToken = $state(false);
	let message = $state('');
	let errors = $state<string[]>([]);
	let submitting = $state(false);

	let username = $state('');
	let email = $state('');
	let departureIata = $state('');
	let currency = $state('');
	let minNights = $state(3);
	let maxNights = $state(7);
	let minDaysAhead = $state(14);
	let maxDaysAhead = $state(90);
	let favorites = $state<string[]>([]);
	let excluded = $state<string[]>([]);

	const cityItems = $derived(
		(refdata?.cities ?? []).map((c) => ({ value: c.code, label: `${c.city} (${c.code})` }))
	);
	const currencyItems = $derived((refdata?.currencies ?? []).map((c) => ({ value: c, label: c })));
	const countryItems = $derived((refdata?.countries ?? []).map((c) => ({ value: c, label: c })));

	onMount(async () => {
		token = new URLSearchParams(location.search).get('token');
		refdata = await (await fetch(`${API_URL}/refdata`)).json();
		if (!token) return;
		const response = await fetch(
			`${API_URL}/subscription?token=${encodeURIComponent(token)}`
		);
		if (!response.ok) {
			invalidToken = true;
			return;
		}
		const current: Subscription = await response.json();
		updating = true;
		username = current.username;
		email = current.email;
		departureIata = current.departure_iata;
		currency = current.currency;
		minNights = current.min_nights;
		maxNights = current.max_nights;
		minDaysAhead = current.min_days_ahead;
		maxDaysAhead = current.max_days_ahead;
		favorites = current.favorites;
		excluded = current.excluded;
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		submitting = true;
		message = '';
		errors = [];
		const payload = {
			username,
			email,
			departure_iata: departureIata,
			currency,
			min_nights: minNights,
			max_nights: maxNights,
			min_days_ahead: minDaysAhead,
			max_days_ahead: maxDaysAhead,
			favorite_countries: favorites,
			excluded_countries: excluded
		};
		const response = updating
			? await fetch(`${API_URL}/subscription?token=${encodeURIComponent(token ?? '')}`, {
					method: 'PUT',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(payload)
				})
			: await fetch(`${API_URL}/subscribe`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(payload)
				});
		submitting = false;
		if (!response.ok) {
			errors = errorMessages(await response.json());
			return;
		}
		message = updating
			? 'Your preferences were changed successfully.'
			: `Almost there! We sent a confirmation link to ${email} — click it to start receiving deals.`;
	}
</script>

<svelte:head>
	<title>Subscribe | Air Nomad Society</title>
	<meta
		name="description"
		content="Join the Air Nomad Society and receive the best flight deals directly in your inbox. Sign up now for free!"
	/>
</svelte:head>

<h1 class="mt-10 text-3xl font-bold">
	{updating ? 'Update your preferences' : 'Become an Air Nomad'}
</h1>

{#if invalidToken}
	<div class="banner banner-error">
		This link is invalid or the subscription no longer exists. You can subscribe again below.
	</div>
{/if}

{#if message}
	<div class="banner banner-success">{message}</div>
{/if}

{#if errors.length}
	<div class="banner banner-error">
		{#each errors as error (error)}
			<div>{error}</div>
		{/each}
	</div>
{/if}

<form onsubmit={submit}>
	<div class="my-6 grid gap-4 sm:grid-cols-2">
		<Field required label="Username" hint="Used to personalize your emails.">
			<input class="input" required minlength="3" maxlength="20" bind:value={username} />
		</Field>
		<Field
			required
			label={updating ? 'Email (cannot be changed)' : 'Email'}
			hint="Where your weekly deals land."
		>
			<input class="input" type="email" required disabled={updating} bind:value={email} />
		</Field>
		<Field required label="Departure city" hint="Your city, or the nearest major one.">
			<SelectMenu items={cityItems} placeholder="Select a city" bind:value={departureIata} />
		</Field>
		<Field required label="Currency" hint="Prices are shown in this currency.">
			<SelectMenu items={currencyItems} placeholder="Select a currency" bind:value={currency} />
		</Field>
		<Field required label="Minimum nights" hint="Shortest trip length, in nights.">
			<input class="input" type="number" min="1" required bind:value={minNights} />
		</Field>
		<Field required label="Maximum nights" hint="Longest trip length, in nights.">
			<input class="input" type="number" min="1" required bind:value={maxNights} />
		</Field>
		<Field required label="Search from (days ahead)" hint="Search starts this many days from now.">
			<input class="input" type="number" min="1" max="365" required bind:value={minDaysAhead} />
		</Field>
		<Field required label="Search to (days ahead)" hint="Search ends this many days from now.">
			<input class="input" type="number" min="1" max="365" required bind:value={maxDaysAhead} />
		</Field>
		<Field required label="Favorite destinations" hint="You get deals for these every week.">
			<SelectMenu items={countryItems} placeholder="Select countries" multiple bind:value={favorites} />
		</Field>
		<Field
			label="Exclude from gems"
			hint="Never picked as random gems. Favorites are unaffected."
		>
			<SelectMenu items={countryItems} placeholder="Select countries" multiple bind:value={excluded} />
		</Field>
	</div>
	<button class="btn" type="submit" disabled={submitting || !refdata}>
		{updating ? 'Update Preferences' : 'Join Air Nomad Society'}
	</button>
</form>
