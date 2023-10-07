const startBtn = document.querySelector(".start-btn");
const stopBtn = document.querySelector(".stop-btn");
const form = document.querySelector(".video-form");

let mediaStream;
let mediaRecorder;

startBtn.addEventListener("click", async (e) => {
  let chunks = [];
  let file_id;
  let count = 0;

  [mediaStream, mediaRecorder] = await createRecorder("video/webm");

  const res = await fetch("http://localhost:8001/upload/new", {
    method: "POST",
    body: JSON.stringify({
      file_type: "webm",
    }),
    headers: {
      "Content-Type": "application/json",
    },
    mode: "cors",
  }).then((res) => res.json());

  console.log(res);
  file_id = res.data.file_id;

  mediaRecorder.ondataavailable = async (e) => {
    let is_final = false;

    console.log("blob: ", count);

    if (e.target.state === "inactive") {
      console.log("final chunk");
      is_final = true;
    }

    chunks.push(e.data);

    if (chunks.length === 3 || e.target.state === "inactive") {
      count = count + 1;

      const blob = new Blob(chunks, {
        type: "video/webm",
      });

      const fd = new FormData();
      fd.append("file_id", file_id);
      fd.set("is_final", is_final);
      fd.append("chunk", blob);
      fd.append("chunk_num", count);

      const res = await fetch("http://localhost:8001/upload/chunks", {
        method: "POST",
        body: fd,
        mode: "cors",
      }).then((res) => res.json());

      console.log(res);
      chunks = [];
    }
  };

  mediaRecorder.onstop = (e) => {
    console.log("recorder stopped");
  };

  mediaRecorder.start(10000);
});

stopBtn.addEventListener("click", async (e) => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    console.log("stop button clicked, stop event fired");
    mediaStream.getTracks().forEach((track) => track.stop());
    await navigator.mediaDevices.getUserMedia({ video: false });
  }
});

async function createRecorder(mimeType) {
  const videoStream = await navigator.mediaDevices.getDisplayMedia({
    video: { mediaSource: "screen" },
    audio: true,
  });
  const audioStream = await navigator.mediaDevices.getUserMedia({
    audio: true,
    video: false,
  });

  const stream = new MediaStream([
    ...videoStream.getVideoTracks(),
    ...audioStream.getAudioTracks(),
  ]);

  const recorder = new MediaRecorder(stream, {
    mimeType: mimeType,
  });

  return [stream, recorder];
}
