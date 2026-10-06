export type Inventory = { size: string; quantity: number }
export type Product = { product_id: string; name: string; garment_type: string; description: string; colors: string[]; search_tags: string[]; image_file_path: string; price: number; inventory: Inventory[]; total_stock: number }
