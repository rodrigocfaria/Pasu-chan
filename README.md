# Pasu-chan
A simple offline password manager that I am creating in my free time (still in development, but it works).

## External dependences
You need to have the following Python modules:
* Kivy
* pycrypto

## How to use
* First, create a empty file with `.pasu` extension.
* Run Pasu-chan (`py Pasu-chan.py`) and load the empty file.
* Create a master password for this file.
* Start use (the UI is self explanatory).

## How it works
The basic triple in this program is `name`, `login`, `password`. I recommend use in this way:
* `name`: this field is automatically decrypted when you load the file. For example, you can type `github`.
* `login`: it is the login information. For example, the email you use in GitHub, like `gituser@gmail.com`. It is not automatically decrypted, you should press the eye button to decrypt and reveal.
* `password`: the password. Works in the same way as `login` field.

To allow this kind of atomicity, all fields are individually [de|en]crypted using AES-256 algorithm in pycrypto, causing some waiting time in both operations. The fields are ALWAYS written encrypted on disk, even the `name` field. All decryption only occurs in RAM, and for `login` and `password`, it occurs individually, at request of the user. In other words, unless the user want, the entire file is not in clear text in RAM.

When you type in any field, the clear text of your input SUBTITUTES the previously encrypted data. Your data is only encrypted when you press the `Save file` button, that encrypts all your data, write it to file in disk, load it again, and decrypts automatically only the `name` fields. Also, if you type, the field becomes orange to warn you that it was modified. Be careful to not overwrite important passwords.

When you press the copy button, that data in decrypted and now it is in clear text in clipboard of your computer (there's no other way). Be careful when using it.

To select any line, just press the grey square on the left. The line will become blue.

## Warning
I AM NOT LIABLE IF YOU LOSE YOUR PASSWORD, DATA, OR IF IT GET STOLEN, OR IF YOUR PC EXPLODES AND YOU DIE. This software was made by me TO ME. This kind of warning should be obvious, but I explicitly write it.  USE AT YOUR OWN FUCKING RISK.
