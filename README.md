# windflower.chroma

Uma rádio musical contínua baseada em uma biblioteca de áudio local. O servidor mantém uma única transmissão ao vivo: todos os dispositivos conectados ao endpoint `/stream` recebem o mesmo áudio.

*Part of the Chroma Flower creative ecosystem.*

## Requisitos

- Python 3.10 ou superior
- FFmpeg instalado e disponível no PATH
- Windows, Linux ou macOS

## Instalação

1. Instale o FFmpeg e confirme que `ffmpeg -version` funciona no terminal.
2. Coloque suas músicas na pasta `music/` ou configure outro caminho em `config/config.json`.
3. Execute `run.bat` no Windows ou `./run.sh` no Linux/macOS.
4. Abra `http://localhost:8000`.

Na primeira execução, o script cria um ambiente virtual e instala as dependências Python.

## Acesso por outros dispositivos

Descubra o IP local do computador que executa a rádio. Em outro dispositivo conectado à mesma rede, abra `http://IP-DO-SERVIDOR:8000`.

O player web toca a transmissão em `/stream`. Também é possível abrir esse endereço em um player compatível com streams MP3.

## Configuração

Edite `config/config.json`:

- `station_name`: nome exibido da estação.
- `music_directory`: caminho da biblioteca de músicas.
- `ffmpeg_path`: executável FFmpeg ou caminho completo.
- `stream_bitrate`: bitrate MP3, por exemplo `192k`.

Caminhos relativos são interpretados a partir do diretório de execução do projeto; para evitar dúvidas, prefira um caminho absoluto para sua biblioteca.

## API inicial

- `GET /api/status` — estado da rádio, faixa atual, ouvintes e quantidade de arquivos.
- `GET /api/library` — lista de faixas detectadas.
- `GET /api/history?limit=30` — histórico recente.
- `POST /api/skip` — pula a faixa atual.
- `GET /stream` — transmissão contínua MP3.

## Comportamento atual

- Varredura recursiva de arquivos de áudio.
- Reprodução aleatória em ciclos sem repetição até esgotar a biblioteca.
- Histórico persistente em SQLite.
- Uma transmissão compartilhada entre os ouvintes conectados.
- Novas faixas são detectadas durante as próximas varreduras.

## Limitações desta versão-base

- O histórico é salvo quando uma faixa começa, não quando termina.
- O botão de pular atua no servidor e afeta todos os ouvintes.
- Não há autenticação: use inicialmente apenas em uma rede confiável.
- A transmissão é HTTP local, sem TLS nem autenticação.
- Se o processo reiniciar, a música atual recomeça e um novo ciclo aleatório é criado.
- O endpoint é uma transmissão ao vivo; ouvintes que conectarem no meio da música entram no ponto atual.
- A interface não extrai tags ID3 ainda; o título inicial é o nome do arquivo.
- A disponibilidade 24/7 depende de manter o computador, o processo e a rede ligados.

## Próximas etapas sugeridas

1. Leitura de tags ID3/FLAC e capas.
2. Fila e programação por categorias.
3. Reconexão automática do player.
4. Serviço de inicialização automática e recuperação após falhas.
5. Acesso remoto seguro e integração com Icecast, se necessário.
