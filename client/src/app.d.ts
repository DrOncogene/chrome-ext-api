// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  type Video = {
    id: string,
    name: string,
    url: string,
    transcribed: boolean,
    completed: boolean,
    uploaded: boolean,
    created_at: string
  }
}

export {};
