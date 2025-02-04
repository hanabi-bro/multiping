# Multi Ping
コマンドラインで並列でpingを実行
任意のディレクトリに配置してPathを通して使うのが推奨。
Pathを通さなくてもアプリディレクトリ上であれば実行は可能。

## Install
### Windows
1. 任意のディレクトリに解凍
2. 解凍したディレクトリにPathを通す
    `c:\opt\apps\mping`に配置した場合
    #### 一時的なPATH追加
    ```powershell
    $env:Path += ";c:\opt\apps\mping"
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
    [Environment]::SetEnvironmentVariable("Path", "$env:Path;c:\opt\apps\mping", "Machine")
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

## Linux
`~/.local/opt/mping`に配置する場合

1. 任意のディレクトリに解凍
    ```bash
    mkdir -p ~/.local/opt
    tar zxf mping_linux.tgx -C ~/.local/opt
    ```
2. パスの通ったディレクトリにsymlink
    ```bash
    ln -s ~/.local/opt/mping/mping ~/.local/bin/.
    ```
   `~/.local/bin`に新たにPATHを追加する場合
    ```bash
    mkdir -p ~/.local/bin
    [[ "$PATH" == *"$HOME/.local/bin"* ]] || export PATH=$PATH:$HOME/.local/bin
    ```
3. PATHの永続化
    ログインシェル(`.bash_pforile`がなければ`.profile`)が推奨だけど、分からない場合は`.bashrc`に追記でもよい
    ```bash
    [[ "$PATH" == *"$HOME/.local/bin"* ]] || export PATH=$PATH:$HOME/.local/bin
    ```

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
mping
```

### コマンド引数で宛先指定
* 「-l」オプションの後に宛先を指定
* カンマ区切りで複数宛先の定可能
```powershell
mping -l 1.1.1.1,yahoo.co.jp
```

### 宛先ファイルを指定
* 「-f」オプションの後にファイルパスを指定
  - 実行ディレクトリからの相対パスかフルパスで指定
```powershell
mping -f c:\opt\data\dst_list.csv
```

## Uninstall
### Windows
`c:\opt\apps\mping`に配置した場合
1. mpingをディレクトリごと削除
   ```powershell
   rmdir c:\opt\apps\mping
   ```
2. 環境変数からPathを削除
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

### linux
`~/.local/opt/mping`に配置した場合
1. アプリをディレクトリごと削除
    ```bash
    rm -IR ~/.local/opt/mping
    ```
2. PATHは不要なら削除