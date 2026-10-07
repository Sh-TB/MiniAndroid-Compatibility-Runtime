use std::fs::{File};
use std::io::{BufWriter, BufReader, Write};

use crate::types::DexClass;

pub fn save_class_to_file(class: &DexClass, path: &str) -> std::io::Result<()> {
    let full_path = "out/".to_owned() + path.rsplit_once(";").expect("Couldnt remove ;").0;
    let json_string = serde_json::to_string(class).expect("Failed to serialize to JSON");
    let dirs = full_path.rsplit_once('/').expect("Filepath is corrupted.");
    std::fs::create_dir_all(dirs.0).expect("Creating directories failed.");
    return std::fs::write(full_path, json_string);
}

pub fn class_file_to_class(path: &str) -> Option<DexClass> {
    let full_path = "out/".to_owned() + path.rsplit_once(";").expect("Couldnt remove ;").0;

    let file = File::open(full_path).expect("Opening file failed");
    let reader = BufReader::new(file);

    // Read the JSON contents of the file as an instance of `User`.
    let class: DexClass = serde_json::from_reader(reader).expect("Parsing content to class failed.");
    return Some(class)
}

pub fn save_strings_to_file(strings: &[(usize, String)], path: &str) -> std::io::Result<()> {
    let file = File::create(path)?;
    let mut writer = BufWriter::new(file);
    for (i, s) in strings {
        writeln!(writer, "{} -> {}", i, s)?;
    }
    Ok(())
}

pub fn convert_vec_u8_to_vec_u16(data: &mut Vec<u8>) -> Result<Vec<u16>, &'static str> {
    Ok(data.chunks_exact(2).map(|c| u16::from_le_bytes(c.try_into().unwrap())).collect())
}

pub fn convert_vec_u8_to_vec_u32(data: &mut Vec<u8>) -> Result<Vec<u32>, &'static str> {
    if data.len() % 4 != 0 {
        return Err("Input Vec<u8> length must be a multiple of 4 for u32 conversion.");
    }
    Ok(data.chunks_exact(4).map(|c| u32::from_le_bytes(c.try_into().unwrap())).collect())
}

pub fn parse_u16(data: &[u8], offset: usize) -> u16 {
    u16::from_le_bytes([data[offset], data[offset + 1]])
}

pub fn parse_i16(data: &[u8], offset: usize) -> i16 {
    i16::from_le_bytes([data[offset], data[offset + 1]])
}

pub fn parse_u32(data: &[u8], offset: usize) -> u32 {
    let available = (data.len() - 1) - offset;
    let mut slice: [u8; 4] = [0; 4];
    for i in 0..4 {
        if offset + i <= available {
            slice[i] = data[offset + i];
        } else {
            slice[i] = 0x00000000
        }
    }

    u32::from_le_bytes(slice)
}

pub fn parse_i32(data: &[u8], offset: usize) -> i32 {
    let available = (data.len() - 1) - offset;
    let mut slice: [u8; 4] = [0; 4];
    for i in 0..4 {
        if offset + i <= available {
            slice[i] = data[offset + i];
        } else {
            slice[i] = 0x00000000
        }
    }
    i32::from_le_bytes(slice)
}

pub fn parse_u64(data: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes([data[offset], data[offset + 1], data[offset + 2], data[offset + 3], data[offset + 4], data[offset + 5], data[offset + 6], data[offset + 7]])
}

pub fn get_lower_bits(value: u8, num_bits: u8) -> u8 {
    let mask = (1 << num_bits) - 1; 

    value & mask
}