# Load balancer menerima HTTPS dari internet
resource "aws_security_group" "lb" {
  name        = "lb-sg"
  description = "Load balancer publik: HTTPS dari internet"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS dari internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Keluar ke mana saja"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sg-lb"
  }
}

# Server aplikasi hanya menerima dari load balancer, memakai referensi security group
resource "aws_security_group" "app" {
  name        = "app-sg"
  description = "Server aplikasi: port 8080 hanya dari load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Port aplikasi dari load balancer"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.lb.id]
  }

  egress {
    description = "Keluar ke mana saja (lewat NAT gateway)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sg-app"
  }
}

# Basis data hanya menerima dari server aplikasi
resource "aws_security_group" "data" {
  name        = "data-sg"
  description = "Basis data: port 5432 hanya dari server aplikasi"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL dari server aplikasi"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = {
    Name = "sg-data"
  }
}
