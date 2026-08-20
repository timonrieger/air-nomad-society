<script lang="ts">
	import { Select } from 'bits-ui';

	type Item = { value: string; label: string };

	let {
		items,
		placeholder = 'Select...',
		multiple = false,
		value = $bindable(multiple ? [] : '')
	}: {
		items: Item[];
		placeholder?: string;
		multiple?: boolean;
		value?: string | string[];
	} = $props();

	const triggerLabel = $derived.by(() => {
		if (multiple) {
			const selected = value as string[];
			return selected.length ? `${selected.length} selected` : placeholder;
		}
		return items.find((item) => item.value === value)?.label ?? placeholder;
	});

	const empty = $derived(multiple ? (value as string[]).length === 0 : !value);
</script>

{#if multiple}
	<Select.Root type="multiple" bind:value={value as string[]}>
		<Select.Trigger class="select-trigger" data-placeholder={empty ? '' : undefined}>
			{triggerLabel}
		</Select.Trigger>
		<Select.Portal>
			<Select.Content class="select-content" sideOffset={4}>
				<Select.Viewport>
					{#each items as item (item.value)}
						<Select.Item class="select-item" value={item.value} label={item.label}>
							{#snippet children({ selected })}
								<span>{item.label}</span>
								{#if selected}<span>✓</span>{/if}
							{/snippet}
						</Select.Item>
					{/each}
				</Select.Viewport>
			</Select.Content>
		</Select.Portal>
	</Select.Root>
{:else}
	<Select.Root type="single" bind:value={value as string}>
		<Select.Trigger class="select-trigger" data-placeholder={empty ? '' : undefined}>
			{triggerLabel}
		</Select.Trigger>
		<Select.Portal>
			<Select.Content class="select-content" sideOffset={4}>
				<Select.Viewport>
					{#each items as item (item.value)}
						<Select.Item class="select-item" value={item.value} label={item.label}>
							{#snippet children({ selected })}
								<span>{item.label}</span>
								{#if selected}<span>✓</span>{/if}
							{/snippet}
						</Select.Item>
					{/each}
				</Select.Viewport>
			</Select.Content>
		</Select.Portal>
	</Select.Root>
{/if}
