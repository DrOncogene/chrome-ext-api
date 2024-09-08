// import browser from 'webextension-polyfill';
console.log('Content script loaded');

let MEDIARECORDER;
let MEDIASTREAM;

/**
 * Asynchronously starts a media recorder with the specified MIME type.
 *
 * @param {string} mimeType - The MIME type of the media to be recorded.
 * @return {Promise<[MediaStream, MediaRecorder]>} A Promise that resolves to an array containing the media stream and media recorder.
 */
async function startRecorder(mimeType) {
  try {
    const screenStream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        displaySurface: 'monitor',
        frameRate: 60.0,
        noiseSuppression: true
      },
      audio: true,
      monitorTypeSurfaces: 'include',
      surfaceSwitching: 'include',
      selfBrowserSurface: 'include',
      systemAudio: 'include'
    });

    const micStream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: false
    });

    const streams = new MediaStream([
      ...screenStream.getVideoTracks(),
      ...micStream.getAudioTracks()]
    );

    const recorder = new MediaRecorder(streams, {
      mimeType: mimeType
    });

    return [
      streams,
      recorder
    ];
  } catch (error) {
    throw error;
  }
}

/**
 * Sends chunks of data to the server for upload.
 *
 * @param {string} file_id - The ID of the video being uploaded.
 * @param {boolean} is_final - Flag indicating if this is the final chunk.
 * @param {Blob} blob - The data chunk to be uploaded.
 * @param {number} chunk_num - The number of the chunk being uploaded.
 */
async function sendChunks(file_id, is_final = false, blob, chunk_num) {
  const fd = new FormData();
  fd.append('file_id', file_id);
  fd.set('is_final', is_final);
  fd.append('chunk', blob);
  fd.append('chunk_num', chunk_num);

  try {
    const res = await fetch('http://localhost:8001/upload/chunks', {
      method: 'POST',
      body: fd,
      mode: 'cors'
    }).then((response) => response.json());
  } catch (error) {
    console.log(error);
  }
}

/**
 * Records a video and sends the chunks to the server for upload.
 *
 * @return {Promise<void>} Promise that resolves when the recording is finished.
 */
async function record(videoName) {
  let file_id;
  let count = 0;
  let chunks = [];

  try {
    const res = await fetch('http://localhost:8001/upload/new', {
      method: 'POST',
      body: JSON.stringify({
        file_type: 'webm',
        name: videoName,
      }),
      headers: {
        'Content-Type': 'application/json'
      },
      mode: 'cors'
    }).then(async (res) => {
      [MEDIASTREAM, MEDIARECORDER] = await startRecorder('video/webm');
      return res.json()
    });

    file_id = res.data.file_id;
  } catch (error) {
    console.error(error);
    return;
  }

  MEDIARECORDER.ondataavailable = async (e) => {
    let is_final = false;
    chunks.push(e.data);

    if (MEDIARECORDER.state === 'inactive') {
      is_final = true;
    }
    if (chunks.length >= 2 || MEDIARECORDER.state === 'inactive') {
      const blob = new Blob(chunks, { type: 'video/webm' });
      await sendChunks(file_id, is_final, blob, count);
      count += 1;
      chunks = [];
    }
  };

  MEDIARECORDER.onstop = (e) => {
    MEDIASTREAM.getTracks().forEach((track) => track.stop());
  };
  MEDIARECORDER.start(10000);
}

chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
  console.log(message.action, sender)
  if (message.action === 'start') {
    await record(message.videoName);
  }
  if (message.action === 'stop') {
    MEDIASTREAM.getTracks().forEach((track) => track.stop());
    MEDIARECORDER.stop();
  }
});
