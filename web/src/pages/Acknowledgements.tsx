import { usePreferences } from "../preferences";

export function Acknowledgements() {
  const { language } = usePreferences();
  const zh = language === "zh";

  return <article className="acknowledgements">
    <p className="kicker">{zh ? "致谢与来源" : "Acknowledgements & sources"}</p>
    <h1>{zh ? "感谢开放的学术基础设施与研究交流" : "With thanks to open scholarly infrastructure"}</h1>
    <p className="intro">{zh
      ? "SecAwardLens 建立在开放的学术数据、会议官方记录和研究社区的经验分享之上。感谢以下平台与研究者为项目提供数据支持和灵感。"
      : "SecAwardLens builds on open scholarly data, official conference records, and ideas shared by the research community. We are grateful to the following platforms and researchers for their data and inspiration."}</p>

    <section className="acknowledgement-section">
      <h2><a href="https://openalex.org/" target="_blank" rel="noreferrer">OpenAlex ↗</a></h2>
      <p>{zh
        ? "感谢 OpenAlex 提供开放的论文实体、主题、机构和引用数据。它是本站当前公开引用统计的主要来源；相关数据会尽量附带提供方、检索时间和论文标识等来源信息。"
        : "We thank OpenAlex for open scholarly entities, topics, affiliations, and citation data. It is the current primary source for citation statistics on this site; published data is accompanied where possible by provider, retrieval time, and paper identifiers."}</p>
    </section>

    <section className="acknowledgement-section">
      <h2><a href="https://www.semanticscholar.org/?utm_source=api" target="_blank" rel="noreferrer">Semantic Scholar ↗</a></h2>
      <p>{zh
        ? "感谢 Allen Institute for AI 的 Semantic Scholar 团队提供学术图谱 API。项目目前使用该服务发现候选论文实体并补充学术元数据，候选匹配仍需经过人工核查。如未来公开 S2 引用数据，项目会尽量清楚标注其来源并遵循适用条款。"
        : "We thank the Semantic Scholar team at the Allen Institute for AI for providing its Academic Graph API. The project currently uses it to discover candidate paper entities and supplement scholarly metadata, with candidate matches subject to human review. If S2 citation data is published in the future, the project will aim to label its source clearly and follow the applicable terms."}</p>
      <p className="acknowledgement-reference">{zh ? "相关论文：" : "Related paper: "}<a href="https://arxiv.org/abs/2301.10140" target="_blank" rel="noreferrer">Kinney et al., “The Semantic Scholar Open Data Platform,” 2023 ↗</a></p>
    </section>

    <section className="acknowledgement-section inspiration-note">
      <h2>{zh ? "灵感来源" : "Inspiration"}</h2>
      <p>{zh
        ? "本项目持续统计顶会获奖论文引用影响的想法，受到 Yepang Liu 一次关于软件工程顶会最佳与杰出论文引用统计分享的启发。感谢他的交流与启发。"
        : "The idea of tracking citation impact for award-winning conference papers over time was inspired by a citation analysis of best and distinguished papers at leading software-engineering conferences shared by Yepang Liu. We appreciate the exchange and inspiration."}</p>
    </section>
  </article>;
}
