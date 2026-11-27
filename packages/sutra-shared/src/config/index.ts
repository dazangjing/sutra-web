/**
 * 全局配置之总目
 *
 * 各子工程多与此层同名之条目（如「一级分类」），故汇于一处，
 * 免于逐端各引。
 */

export { site, nav, type NavItem } from './site.ts';
export {
  collections,
  collectionMap,
  fixedCategories,
  albums,
  topics,
  type Collection,
  type Rule,
  type Accent,
} from './collections.ts';
export type { Album, AlbumSection } from './albums.ts';
export { HOT_READS, type HotRead } from './hot-reads.ts';
export {
  annualCosts,
  annualCostTotal,
  donors,
  donatedTotal,
  balance,
  funding,
  donorYears,
  operationPrinciples,
  fundUsage,
  type Donor,
  type DonorYear,
} from './funding.ts';
export {
  annualCostTotal as infoAnnualCostTotal,
  operationPrinciples as infoOperationPrinciples,
  aboutSections,
  techStack,
  type Donor as InfoDonor,
} from './info.ts';
export { corpusStats, corpusTotals, type CorpusCategory } from './corpus-stats.ts';
export { canonSources, canonTotals, type CanonSource } from './corpus-canon.ts';
export {
  canonLineage,
  lineageEdges,
  lineageMergeEdges,
  lineageColumns,
  lineageSink,
  lineageSite,
  lineageTotals,
  type CanonLineageNode,
  type LineageEdge,
  type LineageColumn,
} from './canon-lineage.ts';
export {
  classification,
  canons,
  distribution,
  distributionTotal,
  type StatRow,
  type CanonRow,
  type DistRow,
} from './tripitaka.ts';
