const audio = document.getElementById("audio");
const playButton = document.getElementById("play-button");
const skipButton = document.getElementById("skip-button");
let playing = false;
let lastTrack = "";

async function refresh() {
  try {
    const [statusRes, historyRes] = await Promise.all([
      fetch("/api/status"), fetch("/api/history?limit=12")
    ]);
    const status = await statusRes.json();
    const history = await historyRes.json();

    document.getElementById("library-count").textContent = status.library_count;
    document.getElementById("listener-count").textContent = status.listeners;
    document.getElementById("broadcast-state").textContent = status.online ? "ONLINE" : "OFFLINE";

    const track = status.current_track;
    const title = track ? track.title : "Aguardando transmissão";
    if (title !== lastTrack) {
      document.getElementById("track-title").textContent = title;
      document.getElementById("track-subtitle").textContent = track ? "Biblioteca local • windflower.chroma" : "Adicione músicas à pasta configurada.";
      lastTrack = title;
    }

    const list = document.getElementById("history-list");
    list.innerHTML = "";
    if (!history.history.length) {
      list.innerHTML = '<li class="empty">Nenhuma música reproduzida ainda.</li>';
    } else {
      history.history.forEach(item => {
        const li = document.createElement("li");
        const name = document.createElement("span");
        name.textContent = item.title;
        const time = document.createElement("time");
        time.textContent = new Date(item.played_at).toLocaleTimeString("pt-BR", {hour:"2-digit",minute:"2-digit"});
        li.append(name, time);
        list.appendChild(li);
      });
    }
  } catch (error) {
    document.getElementById("broadcast-state").textContent = "ERRO";
  }
}

playButton.addEventListener("click", async () => {
  if (!playing) {
    audio.src = "/stream";
    try {
      await audio.play();
      playing = true;
      playButton.textContent = "Ⅱ Pausar";
      document.getElementById("player-state").textContent = "PLAYER ON";
    } catch (error) {
      document.getElementById("player-state").textContent = "NÃO FOI POSSÍVEL INICIAR";
    }
  } else {
    audio.pause();
    playing = false;
    playButton.textContent = "▶ Ouvir transmissão";
    document.getElementById("player-state").textContent = "PLAYER PAUSED";
  }
});

skipButton.addEventListener("click", async () => {
  await fetch("/api/skip", {method:"POST"});
});

audio.addEventListener("error", () => {
  playing = false;
  playButton.textContent = "▶ Ouvir transmissão";
  document.getElementById("player-state").textContent = "STREAM INDISPONÍVEL";
});

refresh();
setInterval(refresh, 4000);
