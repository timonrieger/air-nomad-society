<script lang="ts">
	import { tick } from 'svelte';
	import { Combobox } from 'bits-ui';

	type Item = { value: string; label: string };
	type Group = { label: string; items: Item[] };

	const GROUP_PREFIX = 'group:';

	let {
		items = [],
		groups = [],
		placeholder = 'Select...',
		multiple = false,
		value = $bindable(multiple ? [] : '')
	}: {
		items?: Item[];
		// Grouped mode (multiple only): group rows are selectable and toggle
		// every item in their group.
		groups?: Group[];
		placeholder?: string;
		multiple?: boolean;
		value?: string | string[];
	} = $props();

	let open = $state(false);
	// What the user typed since opening; narrows the option list.
	let search = $state('');
	// The text the input shows, passed as the root's inputValue. bits-ui
	// writes the clicked item's label into the input on every selection and
	// leaves typed text behind on close; this prop re-asserts the intended
	// text over both.
	let display = $state('');

	const flat = $derived(groups.length ? groups.flatMap((group) => group.items) : items);
	const count = $derived(multiple ? (value as string[]).length : 0);
	const inputPlaceholder = $derived(multiple && count ? `${count} selected` : placeholder);

	const query = $derived(search.trim().toLowerCase());
	const matches = (item: Item) => item.label.toLowerCase().includes(query);
	const visibleItems = $derived(query ? items.filter(matches) : items);
	// A group whose own name matches keeps all its items; otherwise it
	// narrows to its matching items and disappears when none are left.
	const visibleGroups = $derived(
		query
			? groups
					.map((group) =>
						group.label.toLowerCase().includes(query)
							? group
							: { label: group.label, items: group.items.filter(matches) }
					)
					.filter((group) => group.items.length)
			: groups
	);
	const noMatches = $derived(groups.length ? !visibleGroups.length : !visibleItems.length);

	const allSelected = (group: Group) =>
		group.items.every((item) => (value as string[]).includes(item.value));

	// Only a *changed* inputValue prop overrides bits-ui's internal input
	// writes, so detour through a zero-width space — invisible, and never
	// equal to either the old text or what bits-ui just wrote.
	async function assertDisplay(text: string) {
		display = text + '\u200B';
		await tick();
		display = text;
	}

	// Group rows carry a sentinel value that never persists: whenever one
	// shows up in the selection it is replaced by toggling its whole group.
	function onValueChange(selected: string | string[]) {
		if (!multiple) return;
		const picked = new Set(selected as string[]);
		for (const group of groups) {
			if (!picked.delete(GROUP_PREFIX + group.label)) continue;
			const drop = allSelected(group);
			for (const item of group.items) picked[drop ? 'delete' : 'add'](item.value);
		}
		value = [...picked];
		assertDisplay(search);
	}

	function onOpenChange(nowOpen: boolean) {
		if (nowOpen) return;
		search = '';
		if (multiple) assertDisplay('');
	}

	// Single mode shows the selected label whenever the menu is closed —
	// including the initial render with a preloaded value.
	$effect(() => {
		if (open || multiple) return;
		const label = flat.find((item) => item.value === value)?.label ?? '';
		if (label !== display) display = label;
	});
</script>

{#snippet option(item: Item, indent: boolean)}
	<Combobox.Item class="select-item {indent ? 'pl-6' : ''}" value={item.value} label={item.label}>
		{#snippet children({ selected })}
			<span>{item.label}</span>
			{#if selected}<span>✓</span>{/if}
		{/snippet}
	</Combobox.Item>
{/snippet}

{#snippet body()}
	<div class="relative">
		<Combobox.Input
			class="select-trigger truncate pr-8 {multiple && count
				? 'placeholder:text-ink'
				: 'placeholder:text-ink-muted'}"
			placeholder={inputPlaceholder}
			autocomplete="off"
			onclick={() => (open = true)}
			oninput={(event) => {
				search = event.currentTarget.value;
				display = event.currentTarget.value;
			}}
			onkeydown={(event) => {
				// A closed combobox sits in the form like a text input; Enter
				// must not submit it.
				if (event.key === 'Enter' && !open) event.preventDefault();
			}}
		/>
		<span class="pointer-events-none absolute inset-y-0 right-3 flex items-center text-ink-muted">
			▾
		</span>
	</div>
	<Combobox.Portal>
		<Combobox.Content class="select-content" sideOffset={4}>
			<Combobox.Viewport>
				{#if groups.length}
					{#each visibleGroups as group (group.label)}
						<Combobox.Item
							class="select-item font-semibold"
							value={GROUP_PREFIX + group.label}
							label={group.label}
						>
							<span>{group.label}</span>
							{#if allSelected(group)}<span>✓</span>{/if}
						</Combobox.Item>
						{#each group.items as item (item.value)}
							{@render option(item, true)}
						{/each}
					{/each}
				{:else}
					{#each visibleItems as item (item.value)}
						{@render option(item, false)}
					{/each}
				{/if}
				{#if noMatches}
					<span class="select-item text-ink-muted">No matches</span>
				{/if}
			</Combobox.Viewport>
		</Combobox.Content>
	</Combobox.Portal>
{/snippet}

{#if multiple}
	<Combobox.Root
		type="multiple"
		bind:value={value as string[]}
		bind:open
		inputValue={display}
		{onValueChange}
		{onOpenChange}
	>
		{@render body()}
	</Combobox.Root>
{:else}
	<Combobox.Root
		type="single"
		bind:value={value as string}
		bind:open
		inputValue={display}
		{onOpenChange}
	>
		{@render body()}
	</Combobox.Root>
{/if}
