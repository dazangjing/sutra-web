/**
 * 站点运营与捐助
 *
 * 本站为完全公益性质：全部语料、导读、站点代码与构建产物均免费公开，
 * 不设付费墙、不设会员、不投放广告、不向读者收取任何阅读费用。
 *
 * 运行成本（年）由公开的捐助覆盖；若捐助不足，差额由维护者自掏腰包补足，
 * 站点功能不因此缩减 —— 这是本站对读者的承诺。
 */

export type Donor = {
  /** 名字或网名 */
  name: string;
  /** 部分脱敏的来源账号（如 z***@example.com、微信 ***88），供捐赠者核对 */
  account: string;
  /** 捐助金额（美元） */
  amount: number;
};

/**
 * 年运行成本（美元）
 *  · hosting：GitHub Pages 托管年费
 *  · token：大模型 API 调用费（语料整理、导读撰写、义理提要生成）
 */
export const annualCosts = [
  {
    item: 'GitHub Pages 托管',
    amount: 252,
    note: '站点托管与流量年费',
  },
  {
    item: '大模型 API（Token）',
    amount: 120,
    note: '语料整理、导读撰写与义理提要生成之模型调用费',
  },
] as const;

export const annualCostTotal = annualCosts.reduce((s, c) => s + c.amount, 0);

/**
 * 捐助明细
 *
 * 账号一律脱敏后公开（保留可核对的特征，不泄露完整联系方式）。
 * 金额单位：美元。
 */
export const donors: Donor[] = [
  { name: '示例·居士', account: 'z***@example.com', amount: 50 },
  { name: '示例·居士', account: '微信 ***88', amount: 30 },
  { name: '示例·善信', account: 'l***@example.org', amount: 20 },
];

export const donatedTotal = donors.reduce((s, d) => s + d.amount, 0);

/** 成本与捐助之差：正数为未覆盖缺口（由维护者自补），负数为结余 */
export const balance = donatedTotal - annualCostTotal;

export const funding = {
  /** 捐助覆盖率（0–1） */
  coverage: annualCostTotal > 0 ? donatedTotal / annualCostTotal : 0,
  donorCount: donors.length,
} as const;

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
      '年运行成本、捐助明细与二者差额皆在本页公开。数字可逐项核对，不作粉饰：托管年费、模型调用费各几何，收到多少捐助，尚缺几何，一目了然。',
  },
  {
    title: '缺口自担',
    detail:
      '若捐助不足以覆盖成本，差额由维护者自掏腰包补足；站点功能不因此缩减，内容更新亦不因此中断。捐助是支持，不是购买。',
  },
] as const;

/** 捐助去向说明 */
export const fundUsage = [
  { item: 'GitHub Pages 托管与流量', note: '静态站点托管、CDN 分发、带宽' },
  { item: '大模型 API 调用', note: '语料整理校订、导读撰写、义理提要生成' },
  { item: '缺口补足', note: '捐助不足年度成本之部分，由维护者自补，不列支' },
] as const;
