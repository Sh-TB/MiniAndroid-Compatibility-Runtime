#![allow(warnings)]

mod interpreter;
mod parser;
mod types;
mod utils;

use std::fs::read;

use crate::{
    interpreter::interpreter::Interpreter, parser::{parser::Parser, strings::parse_string_at_offset},
    types::DexClass, utils::save_class_to_file,
};

fn main() {
    let path = std::env::args().nth(1).expect("no path given");
    let debug_flag = std::env::args().nth(2);
    let mut bytes = read(&path).expect("File not found.");

    let mut parser = Parser::new(bytes, debug_flag.is_some());
    parser.parse();

    println!("\n\n\n");

    // Interpret
    let mut interpreter = Interpreter::new(parser);
    interpreter.interpret();

    // Dump strings
    // parse_strings(data, &container.string_id_items, &container.header_item);
}
