# GODAN（フリックヒント付き）

azooKey公式のGODAN配列に、フリック方向の文字を小さく常時表示するヒントを加えたカスタムタブです。たとえば「K」の上に「Q」、右に「G」が表示されます。

## 読み込み方

1. 次のURLをコピーします。
2. azooKeyアプリの「拡張」→「カスタムタブの管理」→「URLから読み込む」で貼り付け、「保存」を押します。
3. キーボードのタブバーで、読み込んだタブを選びます。標準版は「GODAN（ヒント付き）」です。

```text
https://raw.githubusercontent.com/H4M4CHi-ttr/azookey-godan-flick-hints/main/godan-flick-hints.json
```

[読み込み用JSON](https://raw.githubusercontent.com/H4M4CHi-ttr/azookey-godan-flick-hints/main/godan-flick-hints.json)

## 幅配分を調整した比較版

両手の親指で比較するため、文字キーを広げ、左右の文字列を少し外側へ寄せた試作です。キー間の隙間も狭くなります。読み込むと「GODAN（幅比較）」という別タブになります。

```text
https://raw.githubusercontent.com/H4M4CHi-ttr/azookey-godan-flick-hints/main/godan-android-width.json
```

[比較版の読み込み用JSON](https://raw.githubusercontent.com/H4M4CHi-ttr/azookey-godan-flick-hints/main/godan-android-width.json)

| 項目 | 標準版 | 比較版 |
| --- | --- | --- |
| タブ名 | GODAN（ヒント付き） | GODAN（幅比較） |
| 横の幅配分（左補助・文字3列・右補助） | 1:1:1:1:1 | 4:5:5:5:4 |
| 文字の並び・縦の段数 | GODAN・5段 | GODAN・5段 |
| 入力動作・フリック・ヒント | 公式GODANの入力動作と方向ヒント | 標準版と同じ |

比較版の幅配分は、[旧公開Mozc AndroidのGODAN](https://chromium.googlesource.com/external/mozc/+/19d8234eb93adc4f2d1cba8e1d41adfcb33e695d/src/android/resources_oss/res/xml/kbd_godan_kana.xml#56)の、左右補助キー17.3％・文字キー21.8％を参考にしています。JSONでは横23セルを4・5・5・5・4セルに分け、約17.39％・21.74％の配分を指定しています。表示幅・中心位置・キー間の隙間にはazooKeyの描画計算も反映されます。

調整対象は横の配分です。段ずらし、操作キーの移動、ヒントの文字サイズ変更は含めていません。現行Gboardの寸法とは照合していません。

普段の持ち方・同じ文字サイズとキーボード高さで、2つのタブを交互に試してください。狙ったキーから隣のキーへずれる回数や、狭くなった隙間・ヒントの見やすさを比較できます。

## 標準版の変更内容

- 英字キー14個と空白キーに、元のフリック候補と同じ文字を添えています。
- キー配置、通常入力、フリック入力、長押し、文字の置換処理は公式GODANと同じです。
- 識別子を `godan_flick_hints`、表示名を「GODAN（ヒント付き）」に変え、元のGODANとは別のタブとして読み込めます。
- 補助文字のサイズはazooKeyの既存の `main_and_directions` 表示に従います。色は中央の文字と同じです。

システムキーと削除キーのアイコンは元のままです。

## 確認状況

両方のJSONの構文、方向ラベルの形式、元データとの比較を確認しています。標準版はヒントとタブ名・識別子、比較版はそれらに加えて横の格子数・キーのx位置・幅を変更しています。それ以外のデータは公式GODANと一致しています。比較版は格子の重複・はみ出しがないことも確認しています。

iPhone / iPadでの読み込み、表示や操作は未確認です。

## 出典とライセンス

元データは[azooKey公式GODAN](https://azookey.com/static/custard/godan.json)です。[公式カスタムタブ紹介](https://azookey.com/CustomTabs)も参照してください。

比較元には、[azooKey-siteの固定版](https://github.com/azooKey/azooKey-site/blob/01a4779becc21cabbcb6532c2c8908616dad5817/public/static/custard/godan.json)を使用しました。取得した公式配布ファイルと固定版のSHA-256は同一です。

```text
535bf23c327235b02bab74f6f64881a41db820cf635da38a96758a409a4745a0
```

元データの著作権表示は `Copyright (c) 2024 ensan (Keita Miwa)` です。[元リポジトリのライセンス説明](https://github.com/azooKey/azooKey-site/blob/01a4779becc21cabbcb6532c2c8908616dad5817/README.md)に従い、MITライセンスの全文を [LICENSE](LICENSE) に同梱しています。このリポジトリもMITライセンスで公開しています。
