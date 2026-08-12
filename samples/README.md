# samples/

Her örnek kendi alt-dizininde: `samples/<örnek_id>/` içine FASTQ/FASTA koy.

- **short:** `*_R1.fastq(.gz)` + `*_R2.fastq(.gz)`
- **long:** tek ONT/PacBio FASTQ (adında `ont`/`nanopore`/`long` geçebilir; R1/R2 DEĞİL)
- **hybrid:** short çifti + long dosyası birlikte
- **assembly:** hazır `*.fasta`

Çalıştırma:
```bash
conda activate virusforge
python3 -m virusforge.cli run --sample samples/<örnek_id> --out runs
```

> Örnek verisi git'e girmez (.gitignore). Kullanıcı hangi örneği indireceğini belirtir.
