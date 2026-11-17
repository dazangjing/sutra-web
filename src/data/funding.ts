/**
 * 站点运营与捐助
 *
 * 本站为完全公益性质：全部语料、导读、站点代码与构建产物均免费公开，
 * 不设付费墙、不设会员、不投放广告、不向读者收取任何阅读费用。
 *
 * 运行成本（年）由公开的捐助覆盖；若捐助不足，差额由维护者自掏腰包补足，
 * 站点功能不因此缩减 —— 这是本站对读者的承诺。
 *
 * 金额单位：人民币元（¥）。
 */

export type Donor = {
  /** 名字或网名 */
  name: string;
  /** 部分脱敏的来源账号（如 z***@example.com、微信 ***88），供捐赠者核对 */
  account: string;
  /** 捐助金额（元） */
  amount: number;
  /** 捐助日期（YYYY-MM-DD），用于按时间排序与归年 */
  date: string;
};

/**
 * 年运行成本（元）
 *  · hosting：站点托管年费
 *  · token：大模型 API 调用费（语料整理、导读撰写、义理提要生成）
 */
export const annualCosts = [
  {
    item: '站点托管与流量',
    amount: 1820,
    note: '静态站点托管、CDN 分发与带宽年费',
  },
  {
    item: '大模型 API（Token）',
    amount: 1600,
    note: '语料整理、导读撰写与义理提要生成之模型调用费',
  },
] as const;

export const annualCostTotal = annualCosts.reduce((s, c) => s + c.amount, 0);

/**
 * 捐助明细
 *
 * 账号一律脱敏后公开（保留可核对的特征，不泄露完整联系方式）。
 * 金额单位：元；按日期倒序排列（新者在前）。
 */
export const donors: Donor[] = [
  {
    name: '示例·居士',
    account: 'z***@example.com',
    amount: 0,
    date: '2026-11-17',
  },
];

/** 捐助合计（元） */
export const donatedTotal = donors.reduce((s, d) => s + d.amount, 0);

/** 成本与捐助之差：正数为未覆盖缺口（由维护者自补），负数为结余 */
export const balance = donatedTotal - annualCostTotal;

export const funding = {
  /** 捐助覆盖率（0–1） */
  coverage: annualCostTotal > 0 ? donatedTotal / annualCostTotal : 0,
  donorCount: donors.length,
} as const;

/**
 * 按年度归集的捐助明细
 *
 * 年份降序（新年在前），年内按日期倒序。
 */
export type DonorYear = {
  /** 年份，如 2026 */
  year: string;
  /** 本年捐助小计（元） */
  total: number;
  /** 本年笔数 */
  count: number;
  /** 本年明细（已排序） */
  donors: Donor[];
};

export const donorYears: DonorYear[] = (() => {
  const byYear = new Map<string, Donor[]>();
  for (const d of [...donors].sort((a, b) => b.date.localeCompare(a.date))) {
    const y = d.date.slice(0, 4);
    const list = byYear.get(y);
    if (list) list.push(d);
    else byYear.set(y, [d]);
  }
  return [...byYear.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([year, list]) => ({
      year,
      total: list.reduce((s, d) => s + d.amount, 0),
      count: list.length,
      donors: list,
    }));
})();

/**
 * 运营模式
 *  · 完全公益：读者免阅、免登录、免付费，无任何付费墙与广告
 *  · 开放为公：源码公开于 GitHub，正文依 CBETA 整理本，学习研究自由引用
 *  · 成本公开：年成本、捐助明细、差额皆公开，接受读者核对
 *  · 缺口自担：捐助不足之处由维护者自掏腰包，不减功能、不降质量
 */
export const operationPrinciples = [
  {
    title: '完全公益',
    detail:
      '本站对一切读者免费开放：不设付费墙、不设会员、不投放广告、不要求注册、不向任何阅读行为收费。全部经文、导读、统计与工具皆免费取用。',
  },
  {
    title: '开放为公',
    detail:
      '站点源码与构建流程公开于 GitHub，任何人可检视、可复制、可自行部署。正文依 CBETA 中華電子佛典協會整理本录入，学习与研究自由引用，引用时请核对原典。',
  },
  {
    title: '成本公开',
    detail:
      '年运行成本、捐助明细与捐助进展皆在本页公开。数字可逐项核对，不作粉饰：托管年费、模型调用费各几何，收到多少捐助，尚缺几何，一目了然。',
  },
  {
    title: '缺口自担',
    detail:
      '若捐助不足以覆盖成本，差额由维护者自掏腰包补足；站点功能不因此缩减，内容更新亦不因此中断。捐助是支持，不是购买。',
  },
] as const;

/** 捐助去向说明 */
export const fundUsage = [
  { item: '站点托管与流量', note: '静态站点托管、CDN 分发、带宽' },
  { item: '大模型 API 调用', note: '语料整理校订、导读撰写、义理提要生成' },
  { item: '缺口补足', note: '捐助不足年度成本之部分，由维护者自补，不列支' },
] as const;
