output "vpc_id" {
  description = "ID VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "ID subnet publik"
  value       = [for s in aws_subnet.public : s.id]
}

output "app_subnet_ids" {
  description = "ID subnet aplikasi (privat)"
  value       = [for s in aws_subnet.app : s.id]
}

output "data_subnet_ids" {
  description = "ID subnet data (terisolasi)"
  value       = [for s in aws_subnet.data : s.id]
}

output "nat_gateway_ids" {
  description = "ID NAT gateway, satu per AZ"
  value       = [for n in aws_nat_gateway.nat : n.id]
}
