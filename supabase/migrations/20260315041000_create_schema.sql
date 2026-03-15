CREATE TABLE IF NOT EXISTS categories (
    id serial PRIMARY KEY,
    name varchar(100) NOT NULL UNIQUE,
    slug varchar(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS stores (
    id serial PRIMARY KEY,
    name varchar(150) NOT NULL,
    slug varchar(150) NOT NULL UNIQUE,
    cnpj varchar(20),
    address varchar(255),
    zip_code varchar(20),
    phone varchar(30),
    contact_email varchar(180),
    city varchar(120) NOT NULL,
    neighborhood varchar(120),
    delivery_radius_km float8,
    latitude float8 NOT NULL,
    longitude float8 NOT NULL,
    banner_url varchar(255),
    is_active boolean,
    created_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS users (
    id serial PRIMARY KEY,
    name varchar(120) NOT NULL,
    email varchar(120) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    city varchar(120) NOT NULL,
    latitude float8,
    longitude float8,
    created_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS offers (
    id serial PRIMARY KEY,
    store_id integer NOT NULL REFERENCES stores (id),
    title varchar(150) NOT NULL,
    description varchar(255),
    image_url varchar(255),
    is_active boolean,
    starts_at timestamp without time zone,
    ends_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS orders (
    id serial PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users (id),
    store_id integer NOT NULL REFERENCES stores (id),
    total numeric(10,2) NOT NULL,
    status varchar(50),
    delivery_address varchar(255) NOT NULL,
    created_at timestamp without time zone
);

CREATE TABLE IF NOT EXISTS products (
    id serial PRIMARY KEY,
    store_id integer NOT NULL REFERENCES stores (id),
    category_id integer NOT NULL REFERENCES categories (id),
    name varchar(150) NOT NULL,
    slug varchar(150) NOT NULL,
    description text,
    price numeric(10,2) NOT NULL,
    promotional_price numeric(10,2),
    stock integer,
    image_url varchar(255),
    is_active boolean,
    created_at timestamp without time zone,
    CONSTRAINT uq_store_product_slug UNIQUE (store_id, slug)
);

CREATE TABLE IF NOT EXISTS order_items (
    id serial PRIMARY KEY,
    order_id integer NOT NULL REFERENCES orders (id),
    product_id integer NOT NULL REFERENCES products (id),
    quantity integer NOT NULL,
    unit_price numeric(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_status_logs (
    id serial PRIMARY KEY,
    order_id integer NOT NULL REFERENCES orders (id),
    previous_status varchar(50),
    new_status varchar(50) NOT NULL,
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id integer REFERENCES users (id)
);
