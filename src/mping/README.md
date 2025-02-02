# Multi Ping
コマンドラインで並列でpingを実行
任意のディレクトリに配置してPathを通して使うのが推奨。
Pathを通さなくてもアプリディレクトリ上であれば実行は可能。

## Install
### Windows
1. 任意のディレクトリに解凍
2. 解凍したディレクトリにPathを通す
    `c:\opt\apps\multi_ping`に配置した場合
    #### 一時的なPATH追加
    ```powershell
    $env:Path += ";c:\opt\apps\multi_ping"
    ```
    確認
    ```powershell
    $ENV:Path.Split(";")
    gcm mping
    ```


    #### ユーザ環境変数のPATHに追加
    ```powershell
    [Environment]::SetEnvironmentVariable("Path", "$env:Path", "User")
    ```
    確認
    ```powershell
    [System.Environment]::GetEnvironmentVariable("Path", "User").Split(";")
    ```
    #### システムグローバル
    管理者権限で実行
    ```powershell
    [Environment]::SetEnvironmentVariable("Path", "$env:Path;c:\opt\apps\multi_ping", "Machine")
    ```
    確認
    ```powershell
    [System.Environment]::GetEnvironmentVariable("Path", "Machine").Split(";")
    ```

    #### 現在のセッションにPathを反映
    ```powershell
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    ```
    ```確認
    $ENV:Path.Split(";")
    gcm mping
    ```


## Uninstall
### Windows
1. 環境変数からPathを削除
    `c:\opt\apps\multi_ping`に配置した場合
    確認
    ```powershell
    [System.Environment]::GetEnvironmentVariable("Path", "User").Split(";")
    ```
    削除
    ```powershell
    Set-Item ENV:Path $ENV:Path.Replace("c:\opt\apps\multi_ping", "")
    Set-Item ENV:Path $ENV:Path.Replace(";;", ";")
    [Environment]::SetEnvironmentVariable("Path", "$env:Path", "User")
    ```
    確認
    ```powershell
    [System.Environment]::GetEnvironmentVariable("Path", "User").Split(";")
    ```
    現在のセッションに反映（おまけ）
    ```powershell
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $ENV:Path.Split(";")
    gcm mping
    ```


2. アプリをディレクトリごと削除

## Usage
Powershellまたはコマンドプロンプトで実行してください。
// Pathが通っていない場合は、フルパスまたは相対パスで直接指定すれば実行可能です。
実行ディレクトリに以下が作成されます。
* results: Ping結果ディレクトリ
* destination.csv: 宛先リスト

アプリディレクトリにある`mping.ini`でttlの変更などが可能です。

### destination_list.csvファイルで宛先指定
* デフォルトのdestination_list.csv
  - デフォルトのファイルが無い場合は自動で作成。
```powershell
mping.exe
```

### コマンド引数で宛先指定
* 「-l」オプションの後に宛先を指定
* カンマ区切りで複数宛先の定可能
```powershell
mping.exe -l 1.1.1.1,yahoo.co.jp
```

### 宛先ファイルを指定
* 「-f」オプションの後にファイルパスを指定
  - 実行ディレクトリからの相対パスかフルパスで指定
```powershell
mping.exe  c:\opt\data\dst_list.csv
```
