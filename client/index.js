const startBtn = document.querySelector(".start-btn");
const stopBtn = document.querySelector(".stop-btn");

let stream;
let recorder;
const fr = new FileReader();

startBtn.addEventListener("click", async (e) => {
  stream = await navigator.mediaDevices.getDisplayMedia({
    video: true,
    audio: true,
  });

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
    let rawBytes;
    let blob_count = count;

    // fr.readAsArrayBuffer(e.data);
    // fr.onloadend = (e) => {
    //   rawBytes = e.target.result;
    // };

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
      const fd = new FormData();
      fd.append("file_id", file_id);
      for (let chunk of chunks) {
        fd.append("chunks", chunk.data);
        fd.set("is_final", chunk.is_final);
      }
      fd.append("chunk_num", count);
      console.log(fd);
      // fd.append("chunks", chunk);
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
