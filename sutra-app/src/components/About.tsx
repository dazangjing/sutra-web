import { aboutSections, techStack } from 'sutra-shared/config/info';

interface Props {
  /**
   * 资源之绝对 URL 前缀（`asset://localhost/<绝对路径>/`）。
   *
   * Tauri 之 `asset://` 协议以请求之 `uri.path()` 与 scope（绝对路径 glob）
   * 比对，故须以此绝对前缀拼接，不能自造相对路径。
   * 浏览器预览时无此前缀（空串），故退回同源之路径。
   */
  assetPrefix?: string;
}

/** 关于页：缘起、来源、结构、体例、技术与致谢 */
export default function About({ assetPrefix = '' }: Props) {
  // 桌面端走 asset:// 绝对 URL；预览时走同源路径
  const wechatSrc = assetPrefix
    ? `${assetPrefix}site/wechat.png`
    : '/images/wechat.png';

  return (
    <div className="page-scroll">
      <article className="prose-page">
        <header className="prose-page-head">
          <h1 className="prose-page-title">关于阅藏经</h1>
          <p className="prose-page-sub">缘起、内容来源与体例说明</p>
        </header>

        {aboutSections.map((s) => (
          <section key={s.title} className="prose-section">
            <h2 className="prose-section-title">{s.title}</h2>
            {s.body.map((p, i) => (
              <p key={i} className="prose-para">
                {p}
              </p>
            ))}
          </section>
        ))}

        {/* 微信：搜一搜「阅藏经」即得 */}
        <section className="prose-section">
          <h2 className="prose-section-title">微信</h2>
          <p className="prose-para">
            微信搜一搜「阅藏经」，即可关注本站之公众号。
          </p>
          <figure className="about-wechat">
            <img
              src={wechatSrc}
              alt="阅藏经微信公众号二维码 —— 微信搜一搜「阅藏经」"
              width={1710}
              height={624}
              loading="lazy"
              decoding="async"
            />
            <figcaption>微信搜一搜「阅藏经」</figcaption>
          </figure>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">技术</h2>
          <dl className="tech-list">
            {techStack.map((t) => (
              <div key={t.k} className="tech-item">
                <dt>{t.k}</dt>
                <dd>{t.v}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">许可与出处</h2>
          <p className="prose-para">
            语料：CBETA 中華電子佛典協會 整理本，繁体底本，逐字未改。
            生僻字字形图：CBETA <code>gaiji-CB</code>。
            桌面端与站点代码：MIT。
          </p>
        </section>
      </article>
    </div>
  );
}
