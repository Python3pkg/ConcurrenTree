(function() {
  var getUrlParameter;
  this.arrayFill = function(array, value, count) {
    /* Fills an array with the values returned by value when given an index
    
        Arguments:
            array: the array to be extended
            value: a function returning the value to be appended when given an       
                index, possible index values being between 0 and count exclusive 
                of count
            count: the number of values to append
        
        Returns: 
            The modified array
        
        Notes: 
            For negative values of count, the function will pass negative values 
            starting from 0 and decreasing to count+1, like so
            (function 'f' returns the value given: f = (i) -> i)
            arrayFill [], f, 5
            returns [0, -1, -2, -3, -4]
        
        Examples:
            pad an array with nulls
            arrayFill [], (-> null), 4
                returns [null, null, null, null]
            
            Produce the 6 first square numbers 
            arrayFill [], ((i) -> i * i), 6
                returns [0, 1, 4, 9, 16, 25]
    */

    var i;
    assert(isArray(array), 'array (first argument) must be an array');
    assert(isFunction(value), 'value (second argument) must be a function');
    assert;
    for (i = 0; 0 <= count ? i < count : i > count; 0 <= count ? i++ : i--) {
      array.push(value(i));
    }
    return array;
  };
  this.isArray = function(obj) {
    if (typeof obj === "object") {
      return Object.prototype.toString.call(obj) === "[object Array]";
    } else {
      return false;
    }
  };
  this.isObject = function(obj) {
    if (typeof obj === "object") {
      return Object.prototype.toString.call(obj) === "[object Object]";
    } else {
      return false;
    }
  };
  this.isFunction = function(obj) {
    if (typeof obj === "function") return true;
    if (typeof obj === "object") {
      return Object.prototype.toString.call(obj) === "[object Function]";
    } else {
      return false;
    }
  };
  this.isInteger = function(obj) {
    return isNumber(obj) && Math.floor(obj) === obj;
  };
  this.isNumber = function(obj) {
    return typeof obj === "number";
  };
  this.isBoolean = function(obj) {
    /* tests if an object is a boolean object
        
        Note! This does not test if an object can resolve to a boolean, it 
        tests whether it is a boolean object. 
        This test is equivalent to 
        if obj is true or obj is false then true else false
        
        JS Condition (obj === true || obj === false), not '=='!
    */
    return typeof obj === "boolean";
  };
  this.isString = function(obj) {
    return typeof obj === "string";
  };
  this.range = function(start, end, step) {
    var i, _results;
    if (step == null) step = 1;
    /* returns an array containing integers ranged between start and end,
        with a gap of step between each one.
        
        Arguments: 
            start: the first value in the range, any integer is valid
            end: the final value in the range, any integer is valid
            step: the step between each value in the range, any non-zero integer 
                is valid. (optional, default = 1)
            
        Returns:
            An array containing all integers between start and end (inclusive of 
            start, exclusive of end), where each integer is different by step 
            from the integers adjacent to it in sequence. 
        
        Notes: 
            Step can be either negative or positive, as the function calculates 
            the correct sign by testing whether the value of start or end is 
            greater. 
            This is done by XORing the conditions end < start, step > 0, and 
            changes the sign if this is true. 
        
        Examples:
            range 0, 5
                [0, 1, 2, 3, 4]
            range 5, 0
                [5, 4, 3, 2, 1]
            range 0, 5, 2
                [0, 2, 4]
            range 5, 0, 2
                [5, 3, 1]
    */

    step = (start < end && step > 0) || (start > end && step < 0) ? step : -step;
    _results = [];
    for (i = start; start <= end ? i < end : i > end; i += step) {
      _results.push(i);
    }
    return _results;
  };
  this.urlParameters = function(url) {
    var i, kv, pairs, params, _i, _len;
    if (url == null) url = this.location.href;
    /* extracts a dictionary of url parameters from the given url
        
        Arguments:
            url: a url to parse parameters from. (Optional, default = 
                this.location.href)
        
        Returns:
            An object containing key: value pairs of the url parameters.
            value is null when the parameter has no value (ie y in '...?x=1&y')
        
        Examples: 
            urlParameters 'http://y.tld/?x=1&b=sugar&magic'
                {x: '1', b: 'sugar', magic: null}
            
        Developer:
            This should logically be extended to use the url decode function 
            to decode urlencoded values, and where possible, these values 
            could be unstringified (1 should be 1 not '1', perhaps?)
    */

    params = {};
    pairs = url.slice(url.indexOf('?') + 1).split('&');
    for (_i = 0, _len = pairs.length; _i < _len; _i++) {
      i = pairs[_i];
      kv = i.split('=');
      params[kv[0]] = kv.length > 1 ? kv[1] : null;
    }
    return params;
  };
  this.get_url_variable = getUrlParameter = function(name, def) {
    /* extracts the parameter name from the current page url, or returns def if
        name does not exist.
        
        Arguments:
            name: the name of the url parameter to extract.
            def: a default value to be returned if name does not exist as a 
                parameter value in the page url.
        
        Returns:
            The value of name, or def.
        
        Notes:
            If name exists but has no value, null is returned (see urlParameters
            function).
        
        Examples:
            (in all examples, the page url is 'http://x.tld/?y=dog&n')
            getUrlParameter 'y', 'default'
                'dog'
            getUrlParameter 'n', 'default'
                null
            getUrlParameter 'z', 'default'
                'default'
    */

    var params;
    params = urlParameters();
    if (params[name] !== void 0) {
      return params[name];
    } else {
      return def;
    }
  };
  this.isJSON = function(str) {
    try {
      JSON.parse(str);
      return true;
    } catch (e) {
      return false;
    }
  };
  this.serial = {
    key: function(str) {
      /*
                  Arguments:
                      str: the string to be formed into a key 
                  
                  Returns: 
                      The key formed from the given string 
                  
                  Notes:
                  
                  Examples:
      */
      if (str.length > 10) {
        return str.slice(0, 10) + serial.sum(str.slice(10));
      } else {
        return str;
      }
    },
    modulo: 65536,
    sum: function(str) {
      /* sums the string passed to it
          
          Arguments: 
              str: the string to be summed
          
          Returns:
              the integer sum of the string given
          
          Notes:
              http://stackoverflow.com/q/7538590/473479
          
          Examples:
      */

      var i, s, _ref;
      s = 0;
      for (i = 0, _ref = str.length; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
        s = (s * s + str.charCodeAt(i)) % serial.modulo;
      }
      return s;
    },
    strict: function(obj) {}
  };
  this.assert = function(condition, message) {
    /* throws an error if the condition passed is not true. Optionally provide
        the error message to be thrown.
        
        Arguments:
            condition: a boolean
            message: an error message (optional)
        
        Returns: 
            nothing
        
        Throws: 
            'Assertion error' 
        
        Notes:
            Recommended use is:
            assert this is that, 'error if not'
            
            This is because asserting a definite boolean is reduntant, the 
            error can just be thrown instead of calling assert.
        
        Examples:
            assert (isString str), 'str is not a string!'
    */
    message = message !== "" ? "Assertion error: '" + message + "'" : 'Assertion error';
    if (!condition) throw message;
  };
}).call(this);