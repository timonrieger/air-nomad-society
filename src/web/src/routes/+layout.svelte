<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="mx-auto flex max-w-4xl items-center justify-between px-5 py-4">
	<a class="flex items-center gap-2 font-bold text-ink hover:no-underline" href="/">
		<img src={favicon} alt="" class="size-6" />
		Air Nomad Society
	</a>
	<nav class="flex gap-5">
		<a class="btn px-4 py-2" href="/subscribe">Subscribe</a>
	</nav>
</header>

<main class="mx-auto max-w-4xl px-5">
	{@render children()}
</main>

<footer class="mt-16 border-t border-line py-6 text-center text-sm text-ink-muted">
	<p>Copyright © <a href="https://timonrieger.de">Timon Rieger</a></p>
</footer>
