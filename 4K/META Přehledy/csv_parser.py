"""
CSV Parser for Meta Business Suite exports
Handles parsing of different CSV export types from Meta Business Suite
Supports multiple encodings (UTF-8, UTF-16, Windows-1250, etc.)
"""

import pandas as pd
import os
from datetime import datetime
try:
    import chardet
except ImportError:
    chardet = None

# Models will be imported when needed (to avoid circular imports)
# They should be passed as parameters or imported in the function that uses them


def detect_encoding(filepath):
    """
    Detect the encoding of a file
    Returns the detected encoding
    """
    if chardet is None:
        # If chardet is not available, try common encodings
        for enc in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'windows-1250', 'iso-8859-1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=enc) as test_file:
                    test_file.read(100)
                return enc
            except:
                continue
        return 'utf-8'
    
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            # If confidence is low, try common encodings
            if confidence < 0.7:
                # Try common encodings for Meta Business Suite exports
                for enc in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'windows-1250', 'iso-8859-1', 'cp1252']:
                    try:
                        with open(filepath, 'r', encoding=enc) as test_file:
                            test_file.read(100)
                        return enc
                    except:
                        continue
            
            return encoding if encoding else 'utf-8'
    except Exception as e:
        print(f"Warning: Could not detect encoding, using utf-8: {e}")
        return 'utf-8'


def read_csv_with_encoding(filepath, nrows=None, skiprows=None):
    """
    Read CSV file with automatic encoding detection
    """
    encoding = detect_encoding(filepath)
    
    # Try to read with detected encoding
    # Add UTF-8 with BOM first (common for Meta exports), then UTF-16 variants
    encodings_to_try = ['utf-8-sig', 'utf-8']  # utf-8-sig handles BOM
    if encoding:
        if encoding not in encodings_to_try:
            encodings_to_try.append(encoding)
    encodings_to_try.extend(['utf-16-le', 'utf-16-be', 'utf-16', 'windows-1250', 'iso-8859-1', 'cp1252', 'latin1'])
    
    for enc in encodings_to_try:
        try:
            read_params = {'encoding': enc, 'on_bad_lines': 'skip'}
            if nrows:
                read_params['nrows'] = nrows
            if skiprows is not None:
                read_params['skiprows'] = skiprows
            
            df = pd.read_csv(filepath, **read_params)
            print(f"Successfully read CSV with encoding: {enc}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # If it's not an encoding error, try next encoding anyway
            if 'codec' in str(e).lower() or 'decode' in str(e).lower():
                continue
            else:
                raise Exception(f"Error reading CSV file: {str(e)}")
    
    # If all encodings failed, try with error handling
    try:
        read_params = {'encoding': 'utf-8', 'errors': 'replace', 'on_bad_lines': 'skip'}
        if nrows:
            read_params['nrows'] = nrows
        if skiprows is not None:
            read_params['skiprows'] = skiprows
        df = pd.read_csv(filepath, **read_params)
        print("Warning: Read CSV with error replacement (some characters may be corrupted)")
        return df
    except Exception as e:
        raise Exception(f"Could not read CSV file with any encoding. Last error: {str(e)}")


def detect_csv_type(filepath):
    """
    Detect the type of CSV file based on column names
    Returns: 'followers', 'demographics', 'engagement', 'post_level', or 'unknown'
    """
    try:
        # Check for post-level data format (has Post ID, Views, Reach, Likes, etc.)
        filename = os.path.basename(filepath).lower()
        if 'post id' in filename or 'post_id' in filename:
            # Try to read and check columns
            try:
                df = read_csv_with_encoding(filepath, nrows=3)
                columns = [str(col).lower().strip() for col in df.columns]
                if 'post id' in ' '.join(columns) and ('views' in ' '.join(columns) or 'reach' in ' '.join(columns)):
                    return 'post_level'
            except:
                pass
        # First, try to read the file as text to check for special formats
        # Try UTF-16 first (common for Meta exports)
        # Check for BOM (Byte Order Mark)
        with open(filepath, 'rb') as f:
            first_bytes = f.read(4)
            f.seek(0)
            
            # Check BOM
            if first_bytes.startswith(b'\xff\xfe'):  # UTF-16 LE BOM
                encoding = 'utf-16-le'
            elif first_bytes.startswith(b'\xfe\xff'):  # UTF-16 BE BOM
                encoding = 'utf-16-be'
            else:
                encoding = None
            
            # Try UTF-16 variants
            for enc in ['utf-16-le', 'utf-16-be', 'utf-16']:
                try:
                    f.seek(0)
                    raw_data = f.read(3000)
                    if len(raw_data) > 0:
                        # Skip BOM if present
                        if raw_data.startswith(b'\xff\xfe'):
                            raw_data = raw_data[2:]
                        elif raw_data.startswith(b'\xfe\xff'):
                            raw_data = raw_data[2:]
                        
                        text_sample = raw_data.decode(enc, errors='ignore')
                        
                        # Check for Meta Business Suite Audience format
                        if 'Age & gender' in text_sample or 'Top cities' in text_sample or 'Top countries' in text_sample:
                            print(f"Detected Meta Audience format ({enc})")
                            return 'demographics'
                except (UnicodeDecodeError, UnicodeError, Exception) as e:
                    continue
        
        # Try UTF-8 and other encodings
        for encoding in ['utf-8', 'windows-1250', 'latin1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                    text_sample = f.read(2000)
                    
                    # Check for Meta Business Suite Audience format
                    if 'Age & gender' in text_sample or 'Top cities' in text_sample or 'Top countries' in text_sample:
                        print(f"Detected Meta Audience format ({encoding})")
                        return 'demographics'
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Check filename first (fast and reliable)
        filename = os.path.basename(filepath).lower()
        if 'audience' in filename:
            return 'demographics'
        elif 'follow' in filename or 'follows' in filename:
            return 'followers'
        elif 'visit' in filename or 'visits' in filename:
            return 'visits'
        elif any(keyword in filename for keyword in ['view', 'interaction', 'reach', 'click', 'engagement']):
            return 'engagement'
        
        # Read first few rows to detect structure (try as DataFrame)
        try:
            df = read_csv_with_encoding(filepath, nrows=10)
            columns = [str(col).lower().strip() for col in df.columns]
            all_text = ' '.join(columns) + ' ' + ' '.join([str(val).lower() for val in df.values.flatten()[:20]])
            
            # Check for post-level format (has Post ID, Views, Reach, Likes, etc.)
            if 'post id' in all_text or 'post_id' in all_text:
                if 'views' in all_text or 'reach' in all_text or 'likes' in all_text:
                    return 'post_level'
            
            # Check for follower-related columns
            follower_keywords = ['follower', 'followers', 'follower count', 'new followers', 'lost followers', 'follows']
            if any(keyword in all_text for keyword in follower_keywords):
                return 'followers'
            
            # Check for demographic columns
            demo_keywords = ['age', 'gender', 'location', 'country', 'city', 'demographic', 'audience', 'men', 'women']
            if any(keyword in all_text for keyword in demo_keywords):
                return 'demographics'
            
            # Check for engagement columns
            engagement_keywords = ['engagement', 'interaction', 'impression', 'view', 'reach', 'click', 'visits']
            if any(keyword in all_text for keyword in engagement_keywords):
                return 'engagement'
        except Exception as e:
            print(f"Could not read as DataFrame: {e}")
            # If we can't read as DataFrame, check filename
            if 'audience' in filename or 'demographic' in filename:
                return 'demographics'
            elif 'follower' in filename or 'follow' in filename:
                return 'followers'
            elif 'engagement' in filename or 'interaction' in filename:
                return 'engagement'
        
        return 'unknown'
    except Exception as e:
        raise Exception(f"Error detecting CSV type: {str(e)}")


def detect_platform_from_csv(filepath):
    """Detect platform (facebook/instagram) from CSV file path and content"""
    # First, check the directory path (most reliable for our use case)
    filepath_lower = filepath.lower()
    if 'fb' in filepath_lower or 'facebook' in filepath_lower:
        return 'facebook'
    elif 'ig' in filepath_lower or 'instagram' in filepath_lower:
        return 'instagram'
    
    # Then check filename
    filename = os.path.basename(filepath).lower()
    if 'facebook' in filename or 'fb' in filename:
        return 'facebook'
    elif 'instagram' in filename or 'ig' in filename:
        return 'instagram'
    
    # Try to read file content
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(2000)
            # Try UTF-16 first (common for Meta exports), then UTF-8
            for encoding in ['utf-16-le', 'utf-16-be', 'utf-16', 'utf-8-sig', 'utf-8']:
                try:
                    text = raw_data.decode(encoding, errors='ignore')
                    lines = text.split('\n')[:5]
                    # Check lines for platform name
                    for line in lines:
                        line_lower = line.lower()
                        if 'facebook' in line_lower or 'fb' in line_lower:
                            return 'facebook'
                        elif 'instagram' in line_lower or 'ig' in line_lower:
                            return 'instagram'
                except:
                    continue
    except:
        pass
    
    # Default to instagram
    return 'instagram'


def parse_followers_csv(filepath, db):
    """Parse follower growth CSV file"""
    from models import FollowerSnapshot
    try:
        # Detect platform from CSV content
        default_platform = detect_platform_from_csv(filepath)
        
        # Meta Business Suite format has sep=, and header row
        # First line: sep=,
        # Second line: "Facebook follows" or "Instagram follows"
        # Third line: "Date","Primary"
        # So we need to skip first 2 lines and use the third as header
        df = read_csv_with_encoding(filepath, skiprows=2)
        
        # Normalize column names (case-insensitive, strip whitespace)
        df.columns = [col.strip().lower() for col in df.columns]
        
        # If columns are unnamed, try to fix them
        if len(df.columns) >= 2 and ('unnamed' in str(df.columns[0]).lower() or df.columns[0].startswith('unnamed')):
            # Try reading again with explicit header
            df = read_csv_with_encoding(filepath)
            # Find header row (should be row 2, index 2)
            if len(df) > 2:
                # Use row 2 as header
                df.columns = df.iloc[1]
                df = df.iloc[2:].reset_index(drop=True)
                df.columns = [col.strip().lower() if isinstance(col, str) else str(col).strip().lower() for col in df.columns]
        
        # Map common column name variations
        date_col = None
        follower_col = None
        new_col = None
        lost_col = None
        platform_col = None
        
        for col in df.columns:
            if 'date' in col or 'datum' in col:
                date_col = col
            elif 'follower' in col and 'new' not in col and 'lost' not in col:
                follower_col = col
            elif 'new' in col and 'follower' in col:
                new_col = col
            elif 'lost' in col and 'follower' in col:
                lost_col = col
            elif 'platform' in col or 'account' in col:
                platform_col = col
        
        # For Meta Business Suite format, "Primary" column contains the follower count
        is_primary_format = False
        if not follower_col:
            if 'primary' in df.columns:
                follower_col = 'primary'
                is_primary_format = True
            else:
                # Try to find any numeric column
                for col in df.columns:
                    if col != date_col and df[col].dtype in ['int64', 'float64']:
                        follower_col = col
                        break
        
        if not date_col or not follower_col:
            raise Exception(f"Required columns (date, follower count) not found in CSV. Found columns: {list(df.columns)}")
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=False)
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)
        
        imported = 0
        cumulative_count = {}  # Track cumulative count per platform
        
        for _, row in df.iterrows():
            date_val = row[date_col].date()
            # Use platform from CSV column if available, otherwise use detected platform
            if platform_col and pd.notna(row.get(platform_col)):
                platform = str(row[platform_col]).lower()
            else:
                platform = default_platform
            
            # For Meta Business Suite format, "Primary" column interpretation depends on values
            # If values are small (< 100), it's likely daily new followers
            # If values are large (> 100), it's likely cumulative total
            if is_primary_format or follower_col == 'primary':
                primary_value = int(row[follower_col]) if pd.notna(row[follower_col]) else 0
                lost_followers = int(row[lost_col]) if lost_col and pd.notna(row.get(lost_col, 0)) else 0
                
                # Check if this looks like cumulative (large numbers) or daily (small numbers)
                # Get max value in the column to determine
                # Convert to numeric first, handling any non-numeric values
                df[follower_col] = pd.to_numeric(df[follower_col], errors='coerce')
                max_value = df[follower_col].max()
                
                if pd.notna(max_value) and max_value > 500:
                    # Large numbers = cumulative total followers
                    follower_count = primary_value
                    # Calculate new followers as difference from previous day
                    if platform not in cumulative_count:
                        last_snapshot = FollowerSnapshot.query.filter_by(platform=platform).order_by(FollowerSnapshot.date.desc()).first()
                        if last_snapshot:
                            cumulative_count[platform] = last_snapshot.follower_count
                        else:
                            cumulative_count[platform] = 0
                    
                    new_followers = max(0, follower_count - cumulative_count[platform])
                    cumulative_count[platform] = follower_count
                else:
                    # Small numbers = daily new followers
                    new_followers = primary_value
                    
                    # Initialize cumulative count for this platform if not exists
                    if platform not in cumulative_count:
                        # Check if we already have data for this platform
                        last_snapshot = FollowerSnapshot.query.filter_by(platform=platform).order_by(FollowerSnapshot.date.desc()).first()
                        if last_snapshot:
                            # Use existing total as starting point (for merging multiple files)
                            cumulative_count[platform] = last_snapshot.follower_count
                        else:
                            # No previous data - need to calculate starting value
                            # For Facebook: if we know the current total (19357) and sum of daily new (817),
                            # starting value = current_total - sum_of_daily_new
                            # But we don't have that info here, so we'll start from 0
                            # The fix script will adjust this later
                            cumulative_count[platform] = 0
                    
                    # Calculate new total: previous total + new - lost
                    cumulative_count[platform] = cumulative_count[platform] + new_followers - lost_followers
                    follower_count = cumulative_count[platform]
                    
                    # IMPORTANT: Meta Business Suite "Primary" shows NEW followers per day
                    # The total shown in the app (837) is the CURRENT total, not sum of all new
                    # We need to adjust: if we're importing multiple files, use the most recent
                    # file's cumulative sum as the baseline, then work backwards
            else:
                # Standard format - follower_col contains total count
                follower_count = int(row[follower_col]) if pd.notna(row[follower_col]) else 0
                new_followers = int(row[new_col]) if new_col and pd.notna(row.get(new_col, 0)) else 0
                lost_followers = int(row[lost_col]) if lost_col and pd.notna(row.get(lost_col, 0)) else 0
                # Update cumulative for next iteration
                cumulative_count[platform] = follower_count
            
            # Check if record already exists
            existing = FollowerSnapshot.query.filter_by(
                date=date_val,
                platform=platform
            ).first()
            
            if existing:
                # Update existing record
                existing.follower_count = follower_count
                existing.new_followers = new_followers
                existing.lost_followers = lost_followers
            else:
                # Create new record
                snapshot = FollowerSnapshot(
                    date=date_val,
                    follower_count=follower_count,
                    new_followers=new_followers,
                    lost_followers=lost_followers,
                    platform=platform
                )
                db.session.add(snapshot)
            
            imported += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing followers CSV: {str(e)}")


def parse_demographics_csv(filepath, db):
    """Parse demographics CSV file"""
    from models import Demographics
    try:
        # Detect platform from filepath
        default_platform = detect_platform_from_csv(filepath)
        
        # Check if this is Meta Business Suite Audience format (UTF-16 with sections)
        with open(filepath, 'rb') as f:
            raw_data = f.read(2000)
            try:
                # Try UTF-16 first
                text_sample = raw_data.decode('utf-16-le', errors='ignore')
                if 'Age & gender' in text_sample or 'Top cities' in text_sample or 'Top countries' in text_sample:
                    return parse_meta_audience_csv(filepath, db, default_platform)
            except:
                pass
            try:
                # Try UTF-8
                text_sample = raw_data.decode('utf-8', errors='ignore')
                if 'Age & gender' in text_sample or 'Top cities' in text_sample or 'Top countries' in text_sample:
                    return parse_meta_audience_csv(filepath, db, default_platform)
            except:
                pass
        
        df = read_csv_with_encoding(filepath)
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Map common column name variations
        date_col = None
        age_col = None
        gender_col = None
        location_col = None
        city_col = None
        count_col = None
        
        for col in df.columns:
            if 'date' in col or 'datum' in col:
                date_col = col
            elif 'age' in col:
                age_col = col
            elif 'gender' in col or 'pohlaví' in col:
                gender_col = col
            elif 'location' in col or 'country' in col or 'lokace' in col:
                location_col = col
            elif 'city' in col or 'město' in col:
                city_col = col
            elif 'count' in col or 'number' in col or 'počet' in col:
                count_col = col
        
        if not count_col:
            raise Exception("Count column not found in demographics CSV")
        
        # If no date column, use current date or extract from filename
        if not date_col:
            # Try to extract date from filename
            filename = os.path.basename(filepath)
            # Common patterns: YYYY-MM-DD, YYYYMMDD, etc.
            import re
            date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', filename)
            if date_match:
                default_date = pd.to_datetime(date_match.group(1)).date()
            else:
                default_date = datetime.now().date()
        else:
            default_date = None
        
        imported = 0
        for _, row in df.iterrows():
            if date_col and pd.notna(row.get(date_col)):
                date_val = pd.to_datetime(row[date_col], errors='coerce', dayfirst=True)
                if pd.isna(date_val):
                    date_val = default_date if default_date else datetime.now().date()
                else:
                    date_val = date_val.date()
            else:
                date_val = default_date if default_date else datetime.now().date()
            
            age_range = str(row[age_col]) if age_col and pd.notna(row.get(age_col)) else None
            gender = str(row[gender_col]).lower() if gender_col and pd.notna(row.get(gender_col)) else None
            location = str(row[location_col]) if location_col and pd.notna(row.get(location_col)) else None
            city = str(row[city_col]) if city_col and pd.notna(row.get(city_col)) else None
            count = int(row[count_col]) if pd.notna(row[count_col]) else 0
            
            if count > 0:  # Only import if count is valid
                demo = Demographics(
                    date=date_val,
                    age_range=age_range,
                    gender=gender,
                    location=location,
                    city=city,
                    count=count,
                    platform=default_platform
                )
                db.session.add(demo)
                imported += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing demographics CSV: {str(e)}")


def parse_meta_audience_csv(filepath, db, default_platform='instagram'):
    """Parse Meta Business Suite Audience CSV format (UTF-16 with sections)"""
    from models import Demographics
    try:
        # Read file as UTF-16
        with open(filepath, 'r', encoding='utf-16-le', errors='ignore') as f:
            lines = f.readlines()
        
        # Get current date (or extract from filename)
        default_date = datetime.now().date()
        
        imported = 0
        current_section = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('sep='):
                i += 1
                continue
            
            # Detect section headers (check both quoted and unquoted)
            line_lower = line.lower()
            if 'age & gender' in line_lower or '"age & gender"' in line_lower:
                current_section = 'age_gender'
                i += 1
                continue
            elif 'top cities' in line_lower or '"top cities"' in line_lower:
                current_section = 'cities'
                i += 1
                continue
            elif 'top countries' in line_lower or '"top countries"' in line_lower:
                current_section = 'countries'
                i += 1
                continue
            
            # Parse data rows
            if current_section == 'age_gender':
                # Format: "18-24","3.8","1.1"
                if line.startswith('"') and ',' in line:
                    # Remove quotes and split
                    line_clean = line.strip('"')
                    parts = [p.strip().strip('"') for p in line_clean.split('","')]
                    if len(parts) >= 3 and parts[0] and not parts[0].startswith('"'):
                        age_range = parts[0]
                        try:
                            men_pct = float(parts[1]) if parts[1] else 0
                            women_pct = float(parts[2]) if parts[2] else 0
                            
                            # Store as percentage (we'll use 1000 as base for calculations)
                            base_count = 1000
                            
                            if men_pct > 0:
                                demo = Demographics(
                                    date=default_date,
                                    age_range=age_range,
                                    gender='male',
                                    location='Czech Republic',
                                    count=int(base_count * men_pct / 100),
                                    platform=default_platform
                                )
                                db.session.add(demo)
                                imported += 1
                            
                            if women_pct > 0:
                                demo = Demographics(
                                    date=default_date,
                                    age_range=age_range,
                                    gender='female',
                                    location='Czech Republic',
                                    count=int(base_count * women_pct / 100),
                                    platform=default_platform
                                )
                                db.session.add(demo)
                                imported += 1
                        except (ValueError, IndexError):
                            pass
            
            elif current_section == 'cities':
                # Format: "Prague, Czech Republic","Brno, Czech Republic",...
                # Next line: "8.4","3.7","2.8",...
                if i + 1 < len(lines):
                    cities_line = line
                    percentages_line = lines[i + 1].strip()
                    
                    if cities_line.startswith('"') and percentages_line.startswith('"'):
                        # Remove quotes and split
                        cities_clean = cities_line.strip('"')
                        percentages_clean = percentages_line.strip('"')
                        
                        cities = [c.strip().strip('"') for c in cities_clean.split('","')]
                        percentages = [p.strip().strip('"') for p in percentages_clean.split('","')]
                        
                        for city, pct_str in zip(cities, percentages):
                            try:
                                pct = float(pct_str)
                                if pct > 0:
                                    # Extract city name (before comma)
                                    city_name = city.split(',')[0].strip()
                                    base_count = 1000
                                    
                                    demo = Demographics(
                                        date=default_date,
                                        age_range=None,
                                        gender=None,
                                        location=city,
                                        city=city_name,
                                        count=int(base_count * pct / 100),
                                        platform=default_platform
                                    )
                                    db.session.add(demo)
                                    imported += 1
                            except (ValueError, IndexError):
                                continue
                        # Skip next line as we already processed it
                        i += 1
            
            elif current_section == 'countries':
                # Format: "Czech Republic","Slovakia",...
                # Next line: "95.7","1.5",...
                if i + 1 < len(lines):
                    countries_line = line
                    percentages_line = lines[i + 1].strip()
                    
                    if countries_line.startswith('"') and percentages_line.startswith('"'):
                        # Remove quotes and split
                        countries_clean = countries_line.strip('"')
                        percentages_clean = percentages_line.strip('"')
                        
                        countries = [c.strip().strip('"') for c in countries_clean.split('","')]
                        percentages = [p.strip().strip('"') for p in percentages_clean.split('","')]
                        
                        for country, pct_str in zip(countries, percentages):
                            try:
                                pct = float(pct_str)
                                if pct > 0:
                                    base_count = 1000
                                    
                                    demo = Demographics(
                                        date=default_date,
                                        age_range=None,
                                        gender=None,
                                        location=country,
                                        city=None,
                                        count=int(base_count * pct / 100),
                                        platform=default_platform
                                    )
                                    db.session.add(demo)
                                    imported += 1
                            except (ValueError, IndexError):
                                continue
                        # Skip next line as we already processed it
                        i += 1
            
            i += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing Meta Audience CSV: {str(e)}")


def parse_engagement_csv(filepath, db):
    """Parse engagement metrics CSV file"""
    from models import EngagementMetric
    try:
        # Detect platform from CSV content
        default_platform = detect_platform_from_csv(filepath)
        
        # Meta Business Suite format has sep=, and header row, so skip first 2 rows
        df = read_csv_with_encoding(filepath, skiprows=2)
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Determine metric type from filename
        filename = os.path.basename(filepath).lower()
        
        # Map common column name variations
        date_col = None
        views_col = None
        interactions_col = None
        reach_col = None
        clicks_col = None
        visits_col = None
        platform_col = None
        
        for col in df.columns:
            if 'date' in col or 'datum' in col:
                date_col = col
            elif 'view' in col or 'impression' in col or 'zobrazení' in col:
                views_col = col
            elif 'engagement' in col or 'interaction' in col or 'interakce' in col:
                interactions_col = col
            elif 'reach' in col or 'dosah' in col:
                reach_col = col
            elif 'click' in col or 'kliknutí' in col:
                clicks_col = col
            elif 'visit' in col:
                visits_col = col
            elif 'platform' in col or 'account' in col:
                platform_col = col
        
        # For Meta Business Suite format, "Primary" column contains the metric value
        if 'primary' in df.columns:
            if 'view' in filename:
                views_col = 'primary'
            elif 'interaction' in filename:
                interactions_col = 'primary'
            elif 'reach' in filename:
                reach_col = 'primary'
            elif 'click' in filename:
                clicks_col = 'primary'
            elif 'visit' in filename:
                visits_col = 'primary'
        
        if not date_col:
            raise Exception(f"Date column not found in engagement CSV. Found columns: {list(df.columns)}")
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
        df = df.dropna(subset=[date_col])
        
        imported = 0
        for _, row in df.iterrows():
            date_val = row[date_col].date()
            views = int(row[views_col]) if views_col and pd.notna(row.get(views_col, 0)) else 0
            interactions = int(row[interactions_col]) if interactions_col and pd.notna(row.get(interactions_col, 0)) else 0
            reach = int(row[reach_col]) if reach_col and pd.notna(row.get(reach_col, 0)) else 0
            clicks = int(row[clicks_col]) if clicks_col and pd.notna(row.get(clicks_col, 0)) else 0
            visits = int(row[visits_col]) if visits_col and pd.notna(row.get(visits_col, 0)) else 0
            # Use platform from CSV column if available, otherwise use detected platform
            if platform_col and pd.notna(row.get(platform_col)):
                platform = str(row[platform_col]).lower()
            else:
                platform = default_platform
            
            # Check if record already exists
            existing = EngagementMetric.query.filter_by(
                date=date_val,
                platform=platform
            ).first()
            
            if existing:
                # Update existing record - only update non-zero values to preserve other metrics
                if views > 0:
                    existing.views = views
                if interactions > 0:
                    existing.interactions = interactions
                if reach > 0:
                    existing.reach = reach
                if clicks > 0:
                    existing.clicks = clicks
            else:
                # Create new record
                metric = EngagementMetric(
                    date=date_val,
                    views=views,
                    interactions=interactions,
                    reach=reach,
                    clicks=clicks,
                    platform=platform
                )
                db.session.add(metric)
            
            imported += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing engagement CSV: {str(e)}")


def parse_visits_csv(filepath, db):
    """Parse visits CSV file (profile visits)"""
    from models import EngagementMetric
    try:
        # Detect platform from CSV content or directory
        default_platform = detect_platform_from_csv(filepath)
        
        # Meta Business Suite format - same structure as Follows
        df = read_csv_with_encoding(filepath)
        
        # Check structure - first column might be "sep="
        if len(df.columns) > 0 and 'sep=' in str(df.columns[0]):
            # First row is sep=, second is platform name, third is header
            df.columns = ['date', 'primary']
            df = df.iloc[2:].reset_index(drop=True)
        elif len(df.columns) >= 2 and ('unnamed' in str(df.columns[0]).lower() or df.columns[0].startswith('unnamed')):
            df.columns = ['date', 'primary']
            df = df.iloc[2:].reset_index(drop=True)
        else:
            df = read_csv_with_encoding(filepath, skiprows=2)
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Map columns
        date_col = None
        visits_col = None
        
        for col in df.columns:
            if 'date' in col:
                date_col = col
            elif 'primary' in col:
                visits_col = col
        
        if not date_col or not visits_col:
            raise Exception(f"Required columns (date, visits) not found in CSV. Found columns: {list(df.columns)}")
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=False)
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)
        
        imported = 0
        for _, row in df.iterrows():
            date_val = row[date_col].date()
            visits = int(row[visits_col]) if pd.notna(row.get(visits_col, 0)) else 0
            
            # Check if record already exists
            existing = EngagementMetric.query.filter_by(
                date=date_val,
                platform=default_platform
            ).first()
            
            if existing:
                # Update existing record - add visits
                existing.visits = visits
            else:
                # Create new record
                metric = EngagementMetric(
                    date=date_val,
                    views=0,
                    interactions=0,
                    reach=0,
                    clicks=0,
                    visits=visits,
                    platform=default_platform
                )
                db.session.add(metric)
            
            imported += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing visits CSV: {str(e)}")


def parse_post_level_csv(filepath, db):
    """Parse post-level CSV file (aggregates to daily engagement metrics)"""
    from models import EngagementMetric
    try:
        # Detect platform from CSV content or directory
        default_platform = detect_platform_from_csv(filepath)
        
        # Read CSV file (UTF-8 with BOM is common)
        df = read_csv_with_encoding(filepath)
        
        # Normalize column names
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Map columns
        publish_time_col = None
        views_col = None
        reach_col = None
        likes_col = None
        shares_col = None
        follows_col = None
        comments_col = None
        saves_col = None
        
        for col in df.columns:
            if 'publish time' in col or 'publish_time' in col:
                publish_time_col = col
            elif col == 'views':
                views_col = col
            elif col == 'reach':
                reach_col = col
            elif col == 'likes':
                likes_col = col
            elif col == 'shares':
                shares_col = col
            elif col == 'follows':
                follows_col = col
            elif col == 'comments':
                comments_col = col
            elif col == 'saves':
                saves_col = col
        
        if not publish_time_col:
            raise Exception("Publish time column not found in post-level CSV")
        
        # Parse publish times
        df[publish_time_col] = pd.to_datetime(df[publish_time_col], errors='coerce', dayfirst=False)
        df = df.dropna(subset=[publish_time_col])
        
        # Aggregate by date (publish date)
        df['publish_date'] = df[publish_time_col].dt.date
        
        # Group by date and sum metrics
        agg_dict = {}
        if views_col:
            agg_dict[views_col] = 'sum'
        if reach_col:
            agg_dict[reach_col] = 'sum'
        if likes_col:
            agg_dict[likes_col] = 'sum'
        if shares_col:
            agg_dict[shares_col] = 'sum'
        if follows_col:
            agg_dict[follows_col] = 'sum'
        if comments_col:
            agg_dict[comments_col] = 'sum'
        if saves_col:
            agg_dict[saves_col] = 'sum'
        
        daily_metrics = df.groupby('publish_date').agg(agg_dict).reset_index()
        
        imported = 0
        for _, row in daily_metrics.iterrows():
            date_val = row['publish_date']
            views = int(row[views_col]) if views_col and pd.notna(row.get(views_col, 0)) else 0
            reach = int(row[reach_col]) if reach_col and pd.notna(row.get(reach_col, 0)) else 0
            likes = int(row[likes_col]) if likes_col and pd.notna(row.get(likes_col, 0)) else 0
            comments = int(row[comments_col]) if comments_col and pd.notna(row.get(comments_col, 0)) else 0
            shares = int(row[shares_col]) if shares_col and pd.notna(row.get(shares_col, 0)) else 0
            saves = int(row[saves_col]) if saves_col and pd.notna(row.get(saves_col, 0)) else 0
            
            # Calculate total interactions (likes + comments + shares + saves)
            interactions = likes + comments + shares + saves
            
            # Check if record already exists
            existing = EngagementMetric.query.filter_by(
                date=date_val,
                platform=default_platform
            ).first()
            
            if existing:
                # Update existing record - add to existing values
                existing.views = existing.views + views
                existing.interactions = existing.interactions + interactions
                existing.reach = existing.reach + reach
                existing.clicks = existing.clicks + (shares if shares_col else 0)
            else:
                # Create new record
                metric = EngagementMetric(
                    date=date_val,
                    views=views,
                    interactions=interactions,
                    reach=reach,
                    clicks=shares if shares_col else 0,
                    platform=default_platform
                )
                db.session.add(metric)
            
            imported += 1
        
        db.session.commit()
        return imported
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error parsing post-level CSV: {str(e)}")


def parse_csv_file(filepath, db):
    """
    Main function to parse a CSV file
    Automatically detects the type and parses accordingly
    """
    print(f"Detecting CSV type for: {os.path.basename(filepath)}")
    csv_type = detect_csv_type(filepath)
    print(f"Detected CSV type: {csv_type}")
    
    if csv_type == 'followers':
        imported = parse_followers_csv(filepath, db)
    elif csv_type == 'demographics':
        imported = parse_demographics_csv(filepath, db)
    elif csv_type == 'engagement':
        imported = parse_engagement_csv(filepath, db)
    elif csv_type == 'visits':
        imported = parse_visits_csv(filepath, db)
    elif csv_type == 'post_level':
        imported = parse_post_level_csv(filepath, db)
    else:
        # Try to get more info about the file
        filename = os.path.basename(filepath).lower()
        error_msg = f"Unknown CSV type. Could not detect file type from columns."
        error_msg += f"\nFilename: {filename}"
        
        # Try to read first few bytes to show what we see
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(500)
                error_msg += f"\nFirst 100 bytes (hex): {first_bytes[:100].hex()}"
        except:
            pass
        
        raise Exception(error_msg)
    
    return {
        'type': csv_type,
        'imported': imported,
        'details': {
            'file': os.path.basename(filepath),
            'rows_processed': imported
        }
    }
