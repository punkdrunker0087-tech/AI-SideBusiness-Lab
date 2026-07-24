# 戦略候補キュー（Decision State → Strategy Candidateの最小接続）

> ユーザー提案。フルパイプライン統合（`aqm-strategy`→
> `backtest-framework`→`risk-management`の一気通貫接続）は行わない
> ——「今週RQ-004でPromoteが出たら、今のリポジトリではどこで
> 止まるか」という診断に対する答えが「次にどうすればいいか決まら
> ない」だったため、その1点だけを塞ぐ最小限の接続を作る。他は何も
> 繋がない。

## ルール

- RQのDecisionが**Promote**（Evidence Level E3-R2以上）になった時点で、
  そのRQを本ファイルに1行追記する。それ以外のDecision（Reject・
  Hold・Defer・No Decision Update）は、RQ文書自体・`NEGATIVE_
  RESULTS.md`が完全な記録であり、本ファイルには追記しない
- 追記する情報は最小限: RQ ID・一言説明・Evidence Level・登録日・
  ステータス（`未着手`固定、下記参照）
- **本ファイルはキューであって、実行環境ではない。** ここに載った
  候補を`aqm-strategy`や`backtest-framework`で実際にバックテストする
  作業は、本ファイルの範囲外（次に着手する別作業）
- **フルパイプライン統合への移行基準**: 本キューに5件前後の候補が
  溜まった時点、または「このキューがボトルネックになっている」と
  具体的に確認できた時点で、初めて`aqm-strategy`→
  `backtest-framework`→`risk-management`の統合を検討する。それまでは
  本ファイル（Markdownの手動追記）で十分とし、自動化・スクリプト化は
  行わない

## キュー

| RQ ID | 一言説明 | Evidence | 登録日 | ステータス |
|---|---|---|---|---|
| （まだ登録なし） | | | | |

## なぜこれで十分か

`RESEARCH_UNIT_TEMPLATE.md`は凍結中のため、Decisionの選択肢
（棄却/保留/昇格/再実験/データ不足）自体は変更していない。本ファイルは
その「昇格」という結果を受け取るだけの、テンプレート外の薄い受け皿。
新しいマップでも憲章でもなく、単なる登録簿。
