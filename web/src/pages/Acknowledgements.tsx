import { usePreferences } from "../preferences";

export function Acknowledgements() {
  const { language } = usePreferences();
  const zh = language === "zh";

  return <article className="acknowledgements">
    <p className="kicker">{zh ? "致谢与来源" : "Acknowledgements & sources"}</p>
    <h1>{zh ? "感谢学术基础设施与研究交流" : "With thanks to scholarly infrastructure"}</h1>
    <p className="intro">{zh
      ? "SecAwardLens 建立在学术数据服务、会议官方记录和研究社区的经验分享之上。感谢以下平台与研究者为项目提供数据支持和灵感。"
      : "SecAwardLens builds on scholarly data services, official conference records, and ideas shared by the research community. We are grateful to the following platforms and researchers for their data and inspiration."}</p>

    <section className="acknowledgement-section">
      <h2><a href="https://openalex.org/" target="_blank" rel="noreferrer">OpenAlex ↗</a></h2>
      <p>{zh
        ? "感谢 OpenAlex 提供开放的论文实体、主题、机构和引用数据。相关数据会尽量附带提供方、检索时间和论文标识等来源信息。"
        : "We thank OpenAlex for open scholarly entities, topics, affiliations, and citation data. Published data is accompanied where possible by provider, retrieval time, and paper identifiers."}</p>
    </section>

    <section className="acknowledgement-section">
      <h2><a href="https://www.semanticscholar.org/?utm_source=api" target="_blank" rel="noreferrer">Semantic Scholar ↗</a></h2>
      <p>{zh
        ? "感谢 Allen Institute for AI 的 Semantic Scholar 团队提供学术图谱 API。本站将经过核验的 S2 论文实体与引用观测作为独立数据来源展示，并尽量清楚标注标识、检索时间与适用条款。"
        : "We thank the Semantic Scholar team at the Allen Institute for AI for providing its Academic Graph API. The site displays reviewed S2 paper entities and citation observations as a separate source, with identifiers, retrieval times, and applicable terms labeled where possible."}</p>
      <p className="acknowledgement-reference">{zh ? "相关论文：" : "Related paper: "}<a href="https://arxiv.org/abs/2301.10140" target="_blank" rel="noreferrer">Kinney et al., “The Semantic Scholar Open Data Platform,” 2023 ↗</a></p>
    </section>

    <section className="acknowledgement-section">
      <h2><a href="https://scholar.google.com/" target="_blank" rel="noreferrer">Google Scholar ↗</a> <span>·</span> <a href="https://serpapi.com/google-scholar-api" target="_blank" rel="noreferrer">SerpApi ↗</a> <span>·</span> <a href="https://www.scraperapi.com/" target="_blank" rel="noreferrer">ScraperAPI ↗</a></h2>
      <p>{zh
        ? "Google Scholar 为本站提供更广覆盖的引用观测。由于它没有官方公开 API，项目主要通过 SerpApi 获取结构化结果，并在配额或服务不可用时使用经过验证的 ScraperAPI 后备。观测会标注实际传输服务，并与 OpenAlex、Semantic Scholar 的数据分开呈现。本项目与 Google、SerpApi 或 ScraperAPI 不存在隶属或背书关系。"
        : "Google Scholar supplies a broader citation observation for this site. Because it has no official public API, the project primarily obtains structured results through SerpApi and uses a verified ScraperAPI fallback when quota or service availability requires it. Observations identify the actual transport and remain separate from OpenAlex and Semantic Scholar data. This project is not affiliated with or endorsed by Google, SerpApi, or ScraperAPI."}</p>
    </section>

    <section className="acknowledgement-section inspiration-note">
      <h2>{zh ? "灵感来源" : "Inspiration"}</h2>
      <p>{zh
        ? "本项目持续统计顶会获奖论文引用影响的想法，受到 Yepang Liu 一次关于软件工程顶会最佳与杰出论文引用统计分享的启发。感谢他的交流与启发。"
        : "The idea of tracking citation impact for award-winning conference papers over time was inspired by a citation analysis of best and distinguished papers at leading software-engineering conferences shared by Yepang Liu. We appreciate the exchange and inspiration."}</p>
    </section>
  </article>;
}
