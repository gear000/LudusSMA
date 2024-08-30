variable "aws_region" {
  type        = string
  default     = "eu-west-1"
  description = "AWS Region"
}

variable "tags" {
  type = map(any)
  default = {
    "projectID" = "LudusSMA"
    "rg"        = "foundation"
  }
  description = "Tags"
}

variable "source_repository" {
  type        = string
  default     = "gear000/LudusSMA"
  description = "Source repository"
}

variable "source_branch" {
  type        = string
  default     = "feat/tf_foundation"
  description = "Source branch"
}
