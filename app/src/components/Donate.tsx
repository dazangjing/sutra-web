import {
  annualCostTotal,
  annualCosts,
  balance,
  donatedTotal,
  donors,
  fundUsage,
  operationPrinciples,
} from '../data/info';

const yuan = (n: number) => `¥${n.toLocaleString('en-US')}`;

/** 捐助页：完全公益之承诺、成本公开与捐助明细 */
export default function Donate() {
  return (
    <div className="page-scroll">
      <article className="prose-page">
        <header className="prose-page-head">
          <h1 className="prose-page-title">捐助</h1>
          <p className="prose-page-sub">
            完全公益 · 成本公开 · 缺口自担 —— 捐助纯属自愿，不影响任何阅读权益
          </p>
        </header>

        <section className="prose-section">
          <div className="fund-summary">
            <div className="fund-summary-item">
              <span className="fund-summary-label">年度成本</span>
              <b className="fund-summary-value">{yuan(annualCostTotal)}</b>
            </div>
            <div className="fund-summary-item">
              <span className="fund-summary-label">已收捐助</span>
              <b className="fund-summary-value">{yuan(donatedTotal)}</b>
            </div>
            <div className="fund-summary-item">
              <span className="fund-summary-label">尚缺</span>
              <b className="fund-summary-value is-gap">{yuan(Math.max(0, -balance))}</b>
            </div>
          </div>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">年运行成本</h2>
          <ul className="fund-list">
            {annualCosts.map((c) => (
              <li key={c.item} className="fund-row">
                <span className="fund-row-item">{c.item}</span>
                <span className="fund-row-note">{c.note}</span>
                <span className="fund-row-amount">{yuan(c.amount)}</span>
              </li>
            ))}
          </ul>
          <p className="prose-para prose-para-sm">
            桌面端不产生服务器成本，其分发与更新皆依托既有静态托管。
          </p>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">捐助明细</h2>
          {donors.length === 0 ? (
            <p className="prose-para">尚无捐助记录。</p>
          ) : (
            <ul className="fund-list">
              {donors.map((d, i) => (
                <li key={i} className="fund-row">
                  <span className="fund-row-item">{d.name}</span>
                  <span className="fund-row-note">
                    {d.account} · {d.date}
                  </span>
                  <span className="fund-row-amount">{yuan(d.amount)}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="prose-para prose-para-sm">
            账号一律脱敏后公开，保留可核对的特征，不泄露完整联系方式。
          </p>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">捐助去向</h2>
          <ul className="fund-list">
            {fundUsage.map((u) => (
              <li key={u.item} className="fund-row">
                <span className="fund-row-item">{u.item}</span>
                <span className="fund-row-note">{u.note}</span>
                <span className="fund-row-amount" />
              </li>
            ))}
          </ul>
        </section>

        <section className="prose-section">
          <h2 className="prose-section-title">运营模式</h2>
          <div className="principle-grid">
            {operationPrinciples.map((p) => (
              <div key={p.title} className="principle">
                <div className="principle-title">{p.title}</div>
                <div className="principle-detail">{p.detail}</div>
              </div>
            ))}
          </div>
        </section>
      </article>
    </div>
  );
}
