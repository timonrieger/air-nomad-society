<script lang="ts">
	import { Select } from 'bits-ui';

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

	const flat = $derived(groups.length ? groups.flatMap((group) => group.items) : items);
	const empty = $derived(multiple ? (value as string[]).length === 0 : !value);
	const triggerLabel = $derived(
		empty
			? placeholder
			: multiple
				? `${(value as string[]).length} selected`
				: (flat.find((item) => item.value === value)?.label ?? placeholder)
	);

	const allSelected = (group: Group) =>
		group.items.every((item) => (value as string[]).includes(item.value));

	// Group rows carry a sentinel value that never persists: whenever one shows
	// up in the selection it is replaced by toggling its whole group — selecting
	// every item, or deselecting all of them when all were already selected.
	function expandGroups(selected: string[]) {
		const picked = new Set(selected);
		for (const group of groups) {
			if (!picked.delete(GROUP_PREFIX + group.label)) continue;
			const drop = allSelected(group);
			for (const item of group.items) picked[drop ? 'delete' : 'add'](item.value);
		}
		value = [...picked];
	}
</script>

{#snippet option(item: Item, indent: boolean)}
	<Select.Item class="select-item {indent ? 'pl-6' : ''}" value={item.value} label={item.label}>
		{#snippet children({ selected })}
			<span>{item.label}</span>
			{#if selected}<span>✓</span>{/if}
		{/snippet}
	</Select.Item>
{/snippet}

{#snippet body()}
	<Select.Trigger class="select-trigger" data-placeholder={empty ? '' : undefined}>
		{triggerLabel}
	</Select.Trigger>
	<Select.Portal>
		<Select.Content class="select-content" sideOffset={4}>
			<Select.Viewport>
				{#if groups.length}
					{#each groups as group (group.label)}
						<Select.Item
							class="select-item font-semibold"
							value={GROUP_PREFIX + group.label}
							label={group.label}
						>
							<span>{group.label}</span>
							{#if allSelected(group)}<span>✓</span>{/if}
						</Select.Item>
						{#each group.items as item (item.value)}
							{@render option(item, true)}
						{/each}
					{/each}
				{:else}
					{#each items as item (item.value)}
						{@render option(item, false)}
					{/each}
				{/if}
			</Select.Viewport>
		</Select.Content>
	</Select.Portal>
{/snippet}

{#if multiple}
	<Select.Root type="multiple" bind:value={value as string[]} onValueChange={expandGroups}>
		{@render body()}
	</Select.Root>
{:else}
	<Select.Root type="single" bind:value={value as string}>{@render body()}</Select.Root>
{/if}
