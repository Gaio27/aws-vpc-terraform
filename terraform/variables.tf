variable "region" {
  description = "Region AWS tempat VPC dibuat"
  type        = string
  default     = "ap-southeast-1"
}

variable "name" {
  description = "Nama VPC, dipakai sebagai tag Name"
  type        = string
  default     = "vpc-prod"
}

variable "vpc_cidr" {
  description = "Blok CIDR utama VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "azs" {
  description = "Dua availability zone yang dipakai. Harus berada di region yang sama."
  type        = list(string)
  default     = ["ap-southeast-1a", "ap-southeast-1b"]

  validation {
    condition     = length(var.azs) == 2
    error_message = "Tepat dua availability zone diperlukan."
  }
}
