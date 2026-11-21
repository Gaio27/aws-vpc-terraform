locals {
  # Alamat subnet dihitung dari vpc_cidr supaya tidak ada yang tumpang tindih.
  # Blok /24 indeks 0 dan 1 untuk publik, 10 dan 11 untuk aplikasi, 20 dan 21 untuk data.
  az_letters = { for az in var.azs : az => replace(az, var.region, "") }

  public_subnets = {
    for i, az in var.azs : "publik-${local.az_letters[az]}" => {
      cidr = cidrsubnet(var.vpc_cidr, 8, i)
      az   = az
    }
  }

  app_subnets = {
    for i, az in var.azs : "privat-app-${local.az_letters[az]}" => {
      cidr = cidrsubnet(var.vpc_cidr, 8, 10 + i)
      az   = az
    }
  }

  data_subnets = {
    for i, az in var.azs : "privat-data-${local.az_letters[az]}" => {
      cidr = cidrsubnet(var.vpc_cidr, 8, 20 + i)
      az   = az
    }
  }
}

resource "aws_subnet" "public" {
  for_each = local.public_subnets

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true

  tags = {
    Name = each.key
  }
}

resource "aws_subnet" "app" {
  for_each = local.app_subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = each.key
  }
}

resource "aws_subnet" "data" {
  for_each = local.data_subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = each.key
  }
}
