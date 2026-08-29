export type User = {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: 'bearer'
  user: User
}
