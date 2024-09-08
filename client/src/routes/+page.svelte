<script lang="ts">
  import Loading from 'svelte-material-icons/Loading.svelte';
  import TrayArrowDown from 'svelte-material-icons/TrayArrowDown.svelte';
  import CogOutline from 'svelte-material-icons/CogOutline.svelte';
  // import browser from 'webextension-polyfill';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { videoStore } from '$lib/stores';
  import { expect } from 'vitest';
  import { error } from '@sveltejs/kit';

  onMount(async () => {
    const startBtn = document.querySelector('.start-btn');
    const stopBtn = document.querySelector('.stop-btn');
    const newVidInput = <HTMLInputElement>document.querySelector('.new-vid-input');
    const newVidForm = document.querySelector('.new-vid-form');

    newVidForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.runtime.sendMessage({
        action: 'start',
        videoName: newVidInput.value,
        tab: tab
      });
      console.log('submitted');
    });

    try {
      const resp = await fetch('http://localhost:8001/videos').then((res) => res.json());
      console.log(resp);
      videoStore.set(resp.data);
    } catch (err) {
      console.error(err);
      throw err;
    }
  });
</script>

<nav class="mb-8">
  <ul class="flex flex-nowrap items-center justify-between space-x-3 border-b px-4 pb-4">
    <li>ONCORECORDER</li>
    <li><a href="/settings"><CogOutline width="24" height="24" /></a></li>
  </ul>
</nav>

<section class="mb-8 px-4">
  <h3 class="mb-4 text-lg font-bold">NEW VIDEO</h3>
  <form class="new-vid-form flex flex-nowrap items-center justify-between space-x-2">
    <input
      required
      type="text"
      placeholder="Enter name"
      name="vid-input"
      id=""
      class="new-vid-input h-max w-[200px] rounded-2xl border bg-transparent p-2 px-3"
    />
    <button
      type="submit"
      class="start-btn rounded-md bg-[#faebd7] px-2 py-1 font-semibold text-[#282c34]"
    >
      Record
    </button>
  </form>
</section>

<section class="videos mb-5 px-4">
  <h3 class="mb-4 text-lg font-bold">RETRIEVE YOUR VIDEOS</h3>
  <div class="mb-4">
    <input
      type="text"
      placeholder="Search videos"
      name="search"
      id="search-box"
      class="w-full rounded-2xl border bg-transparent p-2 px-3"
    />
  </div>
  <ul id="videos" class="space-y-2">
    <p class="font-bold italic">Total: {$videoStore.length}</p>
    {#each $videoStore as video (video.id)}
      <li class="flex flex-nowrap items-center justify-between border-b p-2">
        <p class="overflow-hidden text-ellipsis text-nowrap">{video.name}</p>
        <div class="flex space-x-2">
          {#if !video.completed || !video.transcribed}
            <button class="loading-btn hidden">
              <Loading width="24" height="24" class="animate-spin" />
            </button>
          {/if}
          {#if video.completed}
            <a href={`${import.meta.env.VITE_SERVER_URL}${video.url}`} target="_blank"
              ><TrayArrowDown width="24" height="24" /></a
            >
          {/if}
        </div>
      </li>
    {:else}
      <p>No videos found</p>
    {/each}
  </ul>
</section>

<footer class="mt-8">
  <p class="text-center text-xs font-thin italic">Copyright &copy; Oncogene Inc. 2022.</p>
</footer>

<style>
  h3::before {
    content: '';
    display: inline-block;
    width: 1rem;
    height: 0.15rem;
    background-color: #faebd7;
    margin-left: -1rem;
    margin-right: 0.25rem;
    translate: 0 -50%;
    vertical-align: middle;
  }
</style>
