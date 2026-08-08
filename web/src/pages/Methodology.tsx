import { usePreferences } from "../preferences";

export function Methodology({ years = [] }: { years?: number[] }) {
  const { language } = usePreferences();
  const zh = language === "zh";
  const availableYears = [...years].sort((a, b) => b - a).join(", ");
  return <article className="methodology">
    <p className="kicker">{zh ? "指标之前，先讲方法" : "Methods before metrics"}</p>
    <h1>{zh ? "每个数字都应当可追溯" : "Every number should be traceable"}</h1>
    <p className="intro">{zh
      ? "SecAwardLens 将三个容易混淆的对象明确分开：官方奖项决定、规范化学术论文实体，以及引用数据提供方在特定时间给出的观测值。"
      : "SecAwardLens separates three things that are easy to blur together: an official award decision, a canonical scholarly work, and a time-stamped observation from a citation provider."}</p>
    <section><span>01</span><div>
      <h2>{zh ? "奖项信息来自会议组织方" : "Awards come from organizers"}</h2>
      <p>{zh
        ? "奖项数据由会议或主办组织的官方页面整理而来。项目保留页面展示的论文标题、作者、奖项名称、来源 URL、检索时间、解析器版本和提取记录摘要。当前范围仅包括 Best、Outstanding 和 Distinguished Paper，不包括学生奖、工件奖、时间检验奖、海报奖或赞助商奖项。"
        : "The award dataset is curated from conference or sponsoring-organization pages. We preserve the displayed title, authors, award label, source URL, retrieval time, parser version, and a digest of the extracted records. The current scope includes Best, Outstanding, and Distinguished Paper awards—not student, artifact, test-of-time, poster, or sponsor prizes."}</p>
    </div></section>
    <section><span>02</span><div>
      <h2>{zh ? "学术实体一经核验即固定保存" : "Entities are pinned, not rediscovered"}</h2>
      <p>{zh
        ? "匹配优先采用 DOI 精确对应；否则保守地综合论文标题、作者、年份与会议证据。存在歧义时进入人工核验，不自动选择。OpenAlex、Semantic Scholar ID 或 Google Scholar cites_id 一经确认便持久保存；日常刷新直接读取固定标识，不再静默搜索或重新匹配。机器分配的主题与作者机构作为带日期的提供方扩展信息单独保存。"
        : "DOI exact matches are preferred. Otherwise title, authors, year, and venue evidence are scored conservatively. Ambiguity becomes a review item. Once verified, an OpenAlex ID, Semantic Scholar ID, or Google Scholar cites_id is persisted; routine refreshes use that pinned identifier and never silently rematch it. Machine-assigned topics and work affiliations are stored separately as dated provider enrichment."}</p>
    </div></section>
    <section><span>03</span><div>
      <h2>{zh ? "引用快照保持不可变" : "Snapshots remain immutable"}</h2>
      <p>{zh
        ? "引用量是观测值，而不是论文元数据。每条 JSONL 快照记录数据提供方、外部 ID、检索时间、响应摘要与总引用量；若数据源提供，还会记录按引用论文发表年份聚合的数量。每次刷新追加新文件，不改写历史记录。不同提供方的数字始终分开呈现，不相加。"
        : "Citation counts are observations, not paper metadata. Each JSONL snapshot records provider, external ID, retrieval timestamp, response digest, and total count, plus citations grouped by citing publication year when the provider supplies them. New refreshes append a file instead of rewriting history. Counts from different providers remain separate and are never added together."}</p>
    </div></section>
    <section><span>04</span><div>
      <h2>{zh ? "跨会议比较必须说明分母" : "Comparisons acknowledge denominators"}</h2>
      <p>{zh
        ? "会议引用总量首先反映该会议授予了多少篇论文奖。SecAwardLens 优先展示论文级排名、中位数、平均值、四分位数、完整分布，以及固定的发表后三年窗口。样本稀疏的会议与年份组合仍会展示，但不应过度解读。"
        : "Total citations by conference mostly measure how many awards were given. SecAwardLens foregrounds paper-level rankings, median, mean, quartiles, complete distributions, and a fixed first-three-publication-years window. Sparse conference-year groups remain visible but should not be over-interpreted."}</p>
    </div></section>
    <section><span>05</span><div>
      <h2>{zh ? "数据提供方保持可见且相互独立" : "Providers stay visible and independent"}</h2>
      <p>{zh ? <>
        Google Scholar、OpenAlex 与 Semantic Scholar 的收录范围、版本聚合、去重规则和更新时间并不相同，因此同一论文的引用量可能明显不同，也不存在跨平台统一的“真实计数”。本站在有经过核验的 Scholar 快照时默认展示经 SerpApi 获取的 Google Scholar 观测，并允许切换到其他已发布来源。各来源的数值、标识和时间戳保持独立，不相加。Semantic Scholar 观测作为单独署名的数据序列发布，并明确排除在项目的 CC0 声明之外；相关学术成果请参阅 <a href="https://arxiv.org/abs/2301.10140" target="_blank" rel="noreferrer">Kinney 等人的《The Semantic Scholar Open Data Platform》↗</a>。
      </> : <>
        Google Scholar, OpenAlex, and Semantic Scholar differ in coverage, version clustering, deduplication, and update cadence, so the same paper can have substantially different counts; there is no provider-independent “true count.” When verified Scholar snapshots exist, this site defaults to Google Scholar observations retrieved through SerpApi and lets readers switch to other published sources. Counts, identifiers, and timestamps remain separate and are never added together. Semantic Scholar observations are published as a separately attributed series and remain outside the project's CC0 dedication; see <a href="https://arxiv.org/abs/2301.10140" target="_blank" rel="noreferrer">Kinney et al., “The Semantic Scholar Open Data Platform” ↗</a>.
      </>}</p>
    </div></section>
    <aside><strong>{zh ? "当前覆盖" : "Current coverage"}</strong><p>{zh
      ? `${availableYears ? `当前可选年份：${availableYears}。` : "可选年份由数据索引生成。"}只有完成官方来源核验、论文实体匹配和数据验证的年份才会进入首页选择器。未匹配论文会明确显示为暂无引用数据，而不是按零引用处理。`
      : `${availableYears ? `Currently available years: ${availableYears}. ` : "Available years are generated from the data index. "}Only years that have passed official-source review, paper resolution, and data validation enter the homepage selector. Unmatched papers remain visibly unavailable rather than being treated as zero-citation records.`}</p></aside>
  </article>;
}
