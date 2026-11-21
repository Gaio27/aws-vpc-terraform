# AWS VPC dua AZ dengan Terraform

Kode Terraform untuk membuat VPC dengan subnet publik, aplikasi, dan data di dua availability zone, lengkap dengan internet gateway, NAT gateway per AZ, route table, dan security group berbasis referensi. Disertai pemeriksa offline yang memastikan hasil `terraform plan` sesuai aturan desain.

## Masalah

Membuat VPC lewat konsol mudah dilakukan sekali, tetapi sulit diulang dan sulit dijelaskan. Perubahan kecil bisa merusak routing tanpa terlihat. Infrastructure as Code membuat desain bisa ditinjau, diulang, dan dihapus dengan aman.

## Pendekatan

- Terraform dengan provider AWS versi 5.
- Alamat subnet dihitung dengan `cidrsubnet` dari satu CIDR VPC, sehingga tidak ada yang tumpang tindih.
- Satu NAT gateway per AZ, supaya satu zona yang bermasalah tidak memutus akses keluar zona lain.
- Subnet data tidak punya jalur ke internet.
- Security group saling mereferensi, bukan memakai alamat IP tetap.
- `scripts/check_plan.py` memeriksa output `terraform show -json` tanpa memanggil AWS.

## Desain jaringan

| Subnet | CIDR | AZ | Route ke internet |
|---|---|---|---|
| publik-a | 10.20.0.0/24 | ap-southeast-1a | lewat internet gateway |
| publik-b | 10.20.1.0/24 | ap-southeast-1b | lewat internet gateway |
| privat-app-a | 10.20.10.0/24 | ap-southeast-1a | lewat NAT gateway di AZ a |
| privat-app-b | 10.20.11.0/24 | ap-southeast-1b | lewat NAT gateway di AZ b |
| privat-data-a | 10.20.20.0/24 | ap-southeast-1a | tidak ada (hanya rute lokal) |
| privat-data-b | 10.20.21.0/24 | ap-southeast-1b | tidak ada (hanya rute lokal) |

Region yang dipakai adalah ap-southeast-1 (Singapura). Periksa ketersediaan layanan di region tersebut sebelum menerapkan.

## Security group

| Nama | Ingress | Sumber |
|---|---|---|
| sg-lb | TCP 443 | 0.0.0.0/0 (internet) |
| sg-app | TCP 8080 | sg-lb |
| sg-data | TCP 5432 | sg-app |

## Arsitektur

```
terraform/
  main.tf        # provider dan VPC
  variables.tf   # region, CIDR, daftar AZ
  subnets.tf     # subnet publik, aplikasi, dan data
  routing.tf     # IGW, NAT gateway, route table
  security.tf    # security group
  outputs.tf
scripts/
  check_plan.py  # memeriksa aturan desain dari output plan JSON
tests/
  test_check_plan.py
```

## Cara menjalankan

Kode Terraform dibuat dengan hati-hati, tetapi belum divalidasi oleh `terraform validate` di lingkungan pengembangan ini. Jalankan langkah berikut di komputer Anda, dengan akun AWS lab:

```bash
git clone https://github.com/Gaio27/aws-vpc-terraform.git
cd aws-vpc-terraform/terraform

terraform init
terraform validate                       # periksa sintaks dan konfigurasi
terraform plan -out rencana.tfplan       # tinjau perubahan sebelum apply
terraform show -json rencana.tfplan > ../plan.json
cd ..

python3 scripts/check_plan.py plan.json  # periksa aturan desain
pytest -v                                # uji pemeriksa plan

# Setelah plan sesuai, terapkan dan lalu hapus setelah selesai
cd terraform
terraform apply rencana.tfplan
terraform destroy
```

Pemeriksa plan memastikan:
- tepat satu VPC dan enam subnet, semuanya berada di dalam blok VPC,
- tidak ada subnet yang tumpang tindih,
- subnet tersebar di dua AZ,
- subnet publik memberi IP publik dan subnet privat tidak,
- ada satu internet gateway dan dua NAT gateway,
- tidak ada security group yang membuka port selain 443 ke internet.

## Biaya

NAT gateway dikenakan biaya per jam dan per gigabyte. Jalankan proyek ini di akun lab, pasang anggaran dan peringatan biaya, dan jalankan `terraform destroy` setelah selesai.

## Hasil

- [x] `pytest`: 10 pengujian pemeriksa plan lulus
- [ ] `terraform validate`: (isi setelah dijalankan di komputer Anda)
- [ ] `terraform plan` menampilkan jumlah resource: (isi setelah dijalankan)
- [ ] `check_plan.py` menampilkan OK untuk plan sebenarnya: (isi setelah dijalankan)
- [ ] `terraform destroy` berhasil tanpa sisa resource: (isi setelah dijalankan)

## Yang saya pelajari dan akan saya perbaiki

- Tantangan utama adalah urutan dependensi: NAT gateway membutuhkan Elastic IP dan subnet publik lebih dulu, dan route privat menunggu NAT tersedia. Terraform menangani ini lewat referensi antar resource.
- Rencana berikutnya: memakai modul VPC resmi sebagai pembanding, dan menambahkan VPC endpoint untuk S3 agar biaya NAT berkurang.

## Lisensi

MIT
