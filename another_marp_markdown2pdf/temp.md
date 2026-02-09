<div class="mermaid">
flowchart TD
  %% 全体フロー：左→右
  A[〜DR2・AQ0\n設計完了] --> P1o[P1部品発注\n（岩尾判断）]
  P1o --> P1d[P1装機出図（委託法人解除）\nメカ・ソフト検討依頼]
  P1d --> Rv[設計Rv]
  Rv --> P1e[回路P1／本体P1／P1評価]
  P1e --> P2o[P2部品発注\n（岩尾判断）]
  %% P2フェーズ
  subgraph P2[Phase P2]
    direction LR
    P2o --> P2d[P2装機出図（委託法人解除）\nメカ・ソフト検討依頼\nP2組立発行手配]
    P2d --> P2sw[P2ソフト発行（To 回路実装工場）]
    P2sw --> Mv[P2ソフト移行会／P1検査会]
    Mv --> P2e[回路P2／本体P2／P2評価]
    P2e --> Fix[FixRv／P2検査会]
    Fix --> Upd[回路図更新]
  end
  %% 量産準備
  P2e --> ProtoO[量産試作発注\n（要：川さん承認）]
  P2e --> ProtoD[量産装機出図（委託法人解除）\nメカ・ソフト検討依頼\n（必要時：量産評価会資料）]
  %% AQ1以降
  Upd --> AQ1[AQ1「可」直後]
  AQ1 --> Rel[量産図面発行\n（回路図発行／固定一式／PDM）]
</div>

<div style="page-break-before:always"></div>

<div class="mermaid">
flowchart TD
  subgraph U[上流工程（BU・GPRCと連携）]
    A[商品企画連携／仕様・コスト決定] --> B[ベース機種有無確認・選定]
    B --> DR0[DR0]
    DR0 --> C[機能設計／要求仕様Rv]
    C --> D[基板設計（機構担当と連携）]
    D --> DR1[DR1]
    DR1 --> E[試作評価]
    E --> F[設計審査（〜DR2）／設計Rv・図面作成・発行]
  end
  F --> AQ0[AQ0]
  AQ0 --> P1[P1（試験組立）〜評価]
  P1 --> P1fix[P1報告会・FixRv]
  P1fix --> P2[P2（量産試作）〜評価]
  P2 --> P2rep[P2報告会]
  P2rep --> AQ1[AQ1〜量産]
  AQ1 --> AQ2[AQ2〜出荷・開発反省会]
  </div>