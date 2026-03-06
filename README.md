## Hi there 👋

<!--
**oxoxox-oxox/oxoxox-oxox** is a ✨ _special_ ✨ repository because its `README.md` (this file) appears on your GitHub profile.

Here are some ideas to get you started:

- 🔭 I’m currently working on ...
- 🌱 I’m currently learning ...
- 👯 I’m looking to collaborate on ...
- 🤔 I’m looking for help with ...
- 💬 Ask me about ...
- 📫 How to reach me: ...
- 😄 Pronouns: ...
- ⚡ Fun fact: ...
-->


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=250&section=header&text=HI%20THERE!&fontSize=80&fontAlignY=30&animation=twinkling" />
</p>

<p align="center">
  <img src="https://readme-svg-typing-generator.vercel.app/api?lines=I'm%20YourName;Full%20Stack%20Developer;Open%20Source%20Lover&font=Roboto&color=58A6FF&size=25" />
</p>

name: Generate Snake
on:
  schedule:
    - cron: "0 0 * * *" # 每天0点运行
  workflow_dispatch: # 手动触发
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: Platane/snk@v3
        with:
          github_user_name: 你的用户名
          outputs: |
            dist/github-contribution-grid-snake.svg
            dist/github-contribution-grid-snake-dark.svg?palette=github-dark
      - uses: crazy-max/ghaction-github-pages@v3.1.1
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
