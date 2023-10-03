const startBtn = document.querySelector(".start-btn");
const stopBtn = document.querySelector(".stop-btn");

let stream;
let recorder;

startBtn.addEventListener("click", async (e) => {
  const videoStream = await navigator.mediaDevices.getDisplayMedia({
    video: { mediaSource: "screen" },
    audio: true,
  });
  const audioStream = await navigator.mediaDevices.getUserMedia({
    audio: true,
    video: false,
  });

  stream = new MediaStream([
    ...videoStream.getVideoTracks(),
    ...audioStream.getAudioTracks(),
  ]);

  recorder = new MediaRecorder(stream, {
    mimeType: "video/webm",
  });

  let chunks = [];
  let file_id;
  let count = 0;

  const res = await fetch("http://localhost:8001/upload/new", {
    method: "POST",
    body: JSON.stringify({
      file_type: "mp4",
    }),
    headers: {
      "Content-Type": "application/json",
    },
    mode: "cors",
  }).then((res) => res.json());

  console.log(res);
  file_id = res.data.file_id;

  recorder.ondataavailable = async (e) => {
    console.log(e.data.type, count);
    let chunk;
    let blob_count = count;

    if (e.target.state === "inactive") {
      console.log("final chunk");
      chunk = {
        data: e.data,
        blob_num: blob_count + 1,
        is_final: true,
      };
    } else {
      chunk = {
        data: e.data,
        blob_num: blob_count + 1,
        is_final: false,
      };
    }

    chunks.push(chunk);

    if (chunks.length === 3 || e.target.state === "inactive") {
      count = count + 1;
      const blobs = [];
      for (let chunk of chunks) {
        blobs.push(chunk.data);
      }

      const fd = new FormData();
      fd.append("file_id", file_id);
      for (let chunk of chunks) {
        fd.set("is_final", chunk.is_final);
      }
      fd.append("chunk", new Blob(blobs, { type: "video/webm" }));
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

  recorder.onstop = (e) => {
    console.log("recorder stopped");
    stream.getTracks().forEach((track) => track.stop());
  };

  recorder.start(10000);
});

stopBtn.addEventListener("click", (e) => {
  recorder.stop();
});
