// Put the writing target here, as long as it has print() and println() methods
#ifndef gPrinter
  #define gPrinter Serial
#endif

namespace PrintLevel {
	enum PrintLevel {SILENT=0, ERRORS_ONLY, NORMAL_ACKS, ALL_INFO, NUM_SETTINGS};
    char *gStrings[] = {"silent", "error", "ack", "info"};
	PrintLevel gPrintLevel = ALL_INFO;

	const char *toString(PrintLevel p) {
		if(p >= 0 && p < NUM_SETTINGS) return gStrings[p];
		else return gStrings[ALL_INFO];
	}

	const char *toString() { return toString(gPrintLevel); }

	bool set(const char *str) {
	  PrintLevel mode;
	  int i;
	  for(i = 0; i < NUM_SETTINGS; i++) {
		if(!strcmp(str, gStrings[i])) {
		  mode = (PrintLevel)i;
		  break;
		}
	  }

	  if(i == NUM_SETTINGS) {
		/*int mode;
		if(!toInt(arg, &mode) || mode < PrintLevel::ERRORS_ONLY || mode > PrintLevel::ALL_INFO) {
		  printlnError("Error: argument must be between 0 and 3 or one of 'silent', 'error', 'ack', 'info'");
		  return;
		}
		*/
		return false;
	  }
	
	  gPrintLevel = mode;
	  return true;
	}

	void printErrorString() {
		gPrinter.print("Error: argument must one of the following: ");
		for(int i = 0; i < NUM_SETTINGS; i++) {
			gPrinter.print('\'');
			gPrinter.print(gStrings[i]);
			gPrinter.print('\'');
			if(i == NUM_SETTINGS-1) gPrinter.print('\n');
			else gPrinter.print(", ");
		}
	}
}

template<class T>
void printlnAlways(T s) {
  gPrinter.println(s);
}
template<class T>
void printlnError(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::ERRORS_ONLY) return;
  gPrinter.println(s);
}
template<class T>
void printlnAck(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::NORMAL_ACKS) return;
  gPrinter.println(s);
}
template<class T>
void printlnInfo(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::ALL_INFO) return;
  gPrinter.println(s);
}
template<class T>
void printAlways(T s) {
  gPrinter.print(s);
}
template<class T>
void printError(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::ERRORS_ONLY) return;
  gPrinter.print(s);
}
template<class T>
void printAck(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::NORMAL_ACKS) return;
  gPrinter.print(s);
}
template<class T>
void printInfo(T s) {
  if(PrintLevel::gPrintLevel < PrintLevel::ALL_INFO) return;
  gPrinter.print(s);
}

#undef gPrinter
